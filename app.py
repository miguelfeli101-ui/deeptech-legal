from flask import Flask, request, render_template, redirect, jsonify
import hashlib
import datetime
import requests
import io
import PyPDF2
import docx
import os
from PIL import Image
import imagehash
import concurrent.futures  # NUEVO: Importación para Hilos Múltiples (Velocidad)

app = Flask(__name__)

# ==========================================
# CONFIGURACIONES PRINCIPALES
# ==========================================
SERPAPI_KEY = "9c253e2fb00e86510296ff2a44c10d6d7e1ef197344aa602f6e06c5513b0a9ee" 

# Identificador para evitar bloqueos anti-bots
HEADERS_ESTANDAR = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

CARPETA_BOVEDA = 'boveda_local'
try:
    if not os.path.exists(CARPETA_BOVEDA):
        os.makedirs(CARPETA_BOVEDA)
except Exception as e:
    print("Aviso: No se pudo crear la carpeta.")

db_proyectos = []

# ==========================================
# MOTOR 1: IMÁGENES (LENS + REVERSE DORKS CONCURRENTES)
# ==========================================
def comparar_phash_local(imagen_bytes):
    try:
        img = Image.open(io.BytesIO(imagen_bytes))
        nuevo_phash = imagehash.phash(img)
        for proyecto in db_proyectos:
             if 'phash' in proyecto and proyecto['phash']:
                hash_guardado = imagehash.hex_to_hash(proyecto['phash'])
                if nuevo_phash - hash_guardado <= 2: 
                    return True
        return False
    except Exception as e:
        return False

def buscar_imagen_estricta_serpapi(imagen_bytes, nombre_archivo):
    if comparar_phash_local(imagen_bytes):
        return [{"titulo": "Registro Encontrado en Base de Datos Interna", "link": "Plataforma Local", "es_instagram": False, "es_facebook": False}], None

    try:
        img_original = Image.open(io.BytesIO(imagen_bytes))
        phash_original = imagehash.phash(img_original)
    except:
        return None, "Error decodificando imagen."

    # Subida al nodo temporal
    try:
        archivos = {'reqtype': (None, 'fileupload'), 'fileToUpload': (nombre_archivo, imagen_bytes)}
        respuesta_subida = requests.post('https://catbox.moe/user/api.php', files=archivos, headers=HEADERS_ESTANDAR, timeout=15)
        url_publica = respuesta_subida.text.strip()
        if not url_publica.startswith("http"): return None, "Error al generar enlace temporal."
    except requests.exceptions.Timeout: return None, "El nodo temporal tardó demasiado."
    except Exception as e: return None, f"Error de subida: {str(e)}"

    # DEFINICIÓN DE LOS DOS "OJOS" VISUALES
    def fetch_lens():
        params = {"engine": "google_lens", "url": url_publica, "api_key": SERPAPI_KEY}
        try: return requests.get("https://serpapi.com/search.json", params=params, timeout=25).json()
        except: return {}

    def fetch_reverse_dorks():
        params = {
            "engine": "google_reverse_image", 
            "image_url": url_publica, 
            "q": "site:instagram.com OR site:facebook.com", # EL DORK DE META
            "api_key": SERPAPI_KEY
        }
        try: return requests.get("https://serpapi.com/search.json", params=params, timeout=25).json()
        except: return {}

    # EJECUCIÓN PARALELA (VELOCIDAD)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_lens = executor.submit(fetch_lens)
        future_dorks = executor.submit(fetch_reverse_dorks)
        datos_lens = future_lens.result()
        datos_dorks = future_dorks.result()

    if "error" in datos_lens and "error" in datos_dorks: 
        return None, "Error en los motores de búsqueda de imagen."

    plagios_confirmados = []
    links_vistos = set()

    # 1. Analizar resultados de Google Lens (Alta precisión)
    for item in datos_lens.get("exact_matches", []):
        link = item.get("link", "#").lower()
        if link not in links_vistos and link != "#":
            plagios_confirmados.append({
                "titulo": item.get("title", "Coincidencia Exacta Detectada (Lens)"),
                "link": link, "es_instagram": "instagram.com" in link, "es_facebook": "facebook.com" in link
            })
            links_vistos.add(link)

    # 2. Analizar resultados de Reverse Image (Walled Gardens Dorks)
    for item in datos_dorks.get("image_results", []):
        link = item.get("link", "#").lower()
        if link not in links_vistos and link != "#":
            plagios_confirmados.append({
                "titulo": item.get("title", "Copia Exacta en Redes (Radar Profundo)"),
                "link": link, "es_instagram": "instagram.com" in link, "es_facebook": "facebook.com" in link
            })
            links_vistos.add(link)

    # 3. Validación Matemática de Miniaturas Similares (Filtro final)
    for item in datos_lens.get("visual_matches", []):
        link = item.get("link", "#").lower()
        if link in links_vistos: continue
        thumb_url = item.get("thumbnail")
        if thumb_url:
            try:
                res_thumb = requests.get(thumb_url, headers=HEADERS_ESTANDAR, timeout=5)
                if res_thumb.status_code == 200:
                    img_thumb = Image.open(io.BytesIO(res_thumb.content))
                    if phash_original - imagehash.phash(img_thumb) <= 16:
                        plagios_confirmados.append({
                            "titulo": item.get("title", "Copia Idéntica (Verificada por pHash)"),
                            "link": link, "es_instagram": "instagram.com" in link, "es_facebook": "facebook.com" in link
                        })
                        links_vistos.add(link)
            except: pass
        if len(plagios_confirmados) >= 5: break
            
    return plagios_confirmados, None

# ==========================================
# MOTOR 2: DOCUMENTOS (EXTRACCIÓN + DORKS TEXTUALES MULTI-HILO)
# ==========================================
def buscar_documento_con_serpapi(archivo_bytes, nombre_archivo):
    fragmentos_candidatos = []
    extension = nombre_archivo.split('.')[-1].lower()
    
    try:
        if extension == 'pdf':
            lector = PyPDF2.PdfReader(io.BytesIO(archivo_bytes))
            for pagina in lector.pages[:4]:
                texto = pagina.extract_text()
                if texto:
                    fragmentos_candidatos.extend(texto.replace('\n', ' ').split('. '))
        elif extension in ['doc', 'docx']:
            doc = docx.Document(io.BytesIO(archivo_bytes))
            for parrafo in doc.paragraphs[:20]:
                if parrafo.text:
                    fragmentos_candidatos.extend(parrafo.text.replace('\n', ' ').split('. '))
    except Exception as e:
        return None, f"Error al leer documento: {str(e)}"
        
    fragmentos_limpios = [f.strip() for f in fragmentos_candidatos if len(f.split()) > 15]
    if not fragmentos_limpios: return [], None
    fragmentos_limpios.sort(key=lambda x: len(x.split()), reverse=True)
    
    mejor_fragmento = fragmentos_limpios[0]
    fragmento_clave = " ".join(mejor_fragmento.split()[:25])
    
    # ESTRATEGIA DORKS: Creamos 3 consultas distintas
    consultas = [
        f'"{fragmento_clave}"',                                # Ojo 1: Web Global Abierta
        f'"{fragmento_clave}" site:instagram.com',             # Ojo 2: Francotirador Instagram
        f'"{fragmento_clave}" site:facebook.com'               # Ojo 3: Francotirador Facebook
    ]

    # Función auxiliar para que los hilos la ejecuten
    def fetch_texto(q):
        params = {"engine": "google", "q": q, "api_key": SERPAPI_KEY, "hl": "es"}
        try: return requests.get("https://serpapi.com/search.json", params=params, timeout=20).json()
        except: return {}

    resultados_limpios = []
    links_vistos = set()

    # EJECUCIÓN PARALELA DE LAS 3 BÚSQUEDAS (VELOCIDAD)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        resultados_hilos = executor.map(fetch_texto, consultas)
    
    # Unificación de resultados y eliminación de duplicados
    for datos in resultados_hilos:
        if "organic_results" in datos:
            for item in datos["organic_results"][:5]:
                link_encontrado = item.get("link", "#").lower()
                if link_encontrado not in links_vistos and link_encontrado != "#":
                    links_vistos.add(link_encontrado)
                    resultados_limpios.append({
                        "titulo": item.get("title", "Copia Textual Detectada"),
                        "link": item.get("link", "#"),
                        "es_instagram": "instagram.com" in link_encontrado,
                        "es_facebook": "facebook.com" in link_encontrado
                    })
                    
    return resultados_limpios, None

# ==========================================
# ENRUTAMIENTOS Y LÓGICA CORE
# ==========================================

@app.route("/revisar_integridad_hash/<hash_id>", methods=["POST"])
def revisar_integridad_hash(hash_id):
    global db_proyectos
    proyecto = next((p for p in db_proyectos if p['hash_full'] == hash_id), None)
    if not proyecto: return jsonify({"error": "Proyecto no encontrado", "plagio": False}), 404

    ruta_guardado = os.path.join(CARPETA_BOVEDA, proyecto['nombre'])
    if not os.path.exists(ruta_guardado): return jsonify({"error": "El archivo físico no existe", "plagio": False}), 404

    try:
        with open(ruta_guardado, 'rb') as f:
            contenido_binario = f.read()
    except Exception as e: return jsonify({"error": str(e), "plagio": False}), 500

    nombre = proyecto['nombre']
    extension = nombre.split('.')[-1].lower()

    db_proyectos_temporales = [p for p in db_proyectos if p['hash_full'] != hash_id]
    db_original = list(db_proyectos)
    db_proyectos.clear()
    db_proyectos.extend(db_proyectos_temporales)

    sitios_web = []
    try:
        if extension in ['pdf', 'doc', 'docx']:
            sitios_web, error = buscar_documento_con_serpapi(contenido_binario, nombre)
        else:
            sitios_web, error = buscar_imagen_estricta_serpapi(contenido_binario, nombre)
        hay_plagio = True if sitios_web and len(sitios_web) > 0 else False
    finally:
        db_proyectos.clear()
        db_proyectos.extend(db_original)

    for p in db_proyectos:
        if p['hash_full'] == hash_id:
            p['plagio'] = hay_plagio
            break

    return jsonify({"plagio": hay_plagio, "sitios": sitios_web})

@app.route("/eliminar/<hash_id>")
def eliminar_proyecto(hash_id):
    global db_proyectos
    db_proyectos = [p for p in db_proyectos if p['hash_full'] != hash_id]
    return "OK", 200

@app.route("/eliminar_multiples", methods=["POST"])
def eliminar_multiples():
    global db_proyectos
    hashes_a_eliminar = request.form.getlist("hashes[]")
    if hashes_a_eliminar:
        db_proyectos = [p for p in db_proyectos if p['hash_full'] not in hashes_a_eliminar]
    return "OK", 200

@app.route("/renombrar", methods=["POST"])
def renombrar_proyecto():
    hash_id = request.form.get("hash_id")
    nuevo_nombre = request.form.get("nuevo_nombre")
    for p in db_proyectos:
        if p['hash_full'] == hash_id:
            p['nombre'] = nuevo_nombre
            break
    return "OK", 200

@app.route("/", methods=["GET", "POST"])
def index():
    skip_intro = request.args.get("skip_intro") == "true"
    abrir_boveda = request.args.get("boveda") == "true" 
    
    if abrir_boveda: skip_intro = True
    
    if request.method == "POST":
        archivo = request.files.get("archivo")
        if archivo and archivo.filename != '':
            nombre = archivo.filename.replace(" ", "_").replace("/", "")
            contenido_binario = archivo.read()
            hash_sha256 = hashlib.sha256(contenido_binario).hexdigest()
            tiempo_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            extension = nombre.split('.')[-1].lower()
            huella_perceptual = None
            
            if extension in ['pdf', 'doc', 'docx']:
                sitios_web, error = buscar_documento_con_serpapi(contenido_binario, nombre)
                tipo_motor = "Motor NLP Multi-Hilo & Dorks de Redes"
            else:
                try:
                    img_hash = imagehash.phash(Image.open(io.BytesIO(contenido_binario)))
                    huella_perceptual = str(img_hash)
                except: pass
                
                sitios_web, error = buscar_imagen_estricta_serpapi(contenido_binario, nombre)
                tipo_motor = "Validación Cruzada Concurrente & Dorks de Redes"

            hay_plagio = True if sitios_web and len(sitios_web) > 0 else False
            
            if not hay_plagio:
                try:
                    ruta_guardado = os.path.join(CARPETA_BOVEDA, nombre)
                    with open(ruta_guardado, 'wb') as f:
                        f.write(contenido_binario)
                except Exception as e: print("Aviso de guardado:", e)
                
                db_proyectos.insert(0, {
                    "nombre": nombre, "hash": hash_sha256[:12] + "...", 
                    "hash_full": hash_sha256, "phash": huella_perceptual, 
                    "plagio": hay_plagio, "timestamp": tiempo_actual
                })
            
            return render_template('index.html', mostrando_resultado=True, paginas_encontradas=sitios_web, 
                                   error_api=error, hash_resultado=hash_sha256, nombre_archivo=nombre, 
                                   tipo_motor=tipo_motor, timestamp=tiempo_actual, skip_intro=True, 
                                   proyectos=db_proyectos, mostrar_boveda=False) 
            
    return render_template('index.html', mostrando_resultado=False, skip_intro=skip_intro, 
                           proyectos=db_proyectos, mostrar_boveda=abrir_boveda)

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
