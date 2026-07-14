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

app = Flask(__name__)

# ==========================================
# CONFIGURACIONES PRINCIPALES
# ==========================================
SERPAPI_KEY = "9c253e2fb00e86510296ff2a44c10d6d7e1ef197344aa602f6e06c5513b0a9ee" 

# Crear carpeta de Bóveda Local a prueba de fallos
CARPETA_BOVEDA = 'boveda_local'
try:
    if not os.path.exists(CARPETA_BOVEDA):
        os.makedirs(CARPETA_BOVEDA)
except Exception as e:
    print("Aviso: No se pudo crear la carpeta, pero la simulación en memoria continuará.")

# Base de datos simulada en memoria
db_proyectos = []

# ==========================================
# MOTOR 1: IMÁGENES (VALIDACIÓN CRUZADA DE ALTA PRECISIÓN)
# ==========================================
def comparar_phash_local(imagen_bytes):
    try:
        img = Image.open(io.BytesIO(imagen_bytes))
        nuevo_phash = imagehash.phash(img)
        
        for proyecto in db_proyectos:
             if 'phash' in proyecto and proyecto['phash']:
                hash_guardado = imagehash.hex_to_hash(proyecto['phash'])
                distancia = nuevo_phash - hash_guardado
                
                if distancia <= 2: 
                    return True
        return False
    except Exception as e:
        print("Error en pHash:", e)
        return False

def buscar_imagen_estricta_serpapi(imagen_bytes, nombre_archivo):
    if comparar_phash_local(imagen_bytes):
        resultado_local = [{
            "titulo": "Registro Encontrado en Base de Datos Interna",
            "link": "Plataforma Local",
            "es_instagram": False,
            "es_facebook": False
        }]
        return resultado_local, None

    try:
        img_original = Image.open(io.BytesIO(imagen_bytes))
        phash_original = imagehash.phash(img_original)
    except Exception as e:
        return None, "Error decodificando imagen."

    try:
        archivos = {'reqtype': (None, 'fileupload'), 'fileToUpload': (nombre_archivo, imagen_bytes)}
        respuesta_subida = requests.post('https://catbox.moe/user/api.php', files=archivos)
        url_publica = respuesta_subida.text.strip()
        if not url_publica.startswith("http"):
            return None, "No se pudo generar el enlace temporal para el radar."
    except Exception as e:
        return None, f"Error de subida al nodo: {str(e)}"

    try:
        params = {"engine": "google_lens", "url": url_publica, "api_key": SERPAPI_KEY}
        respuesta_serpapi = requests.get("https://serpapi.com/search.json", params=params)
        datos = respuesta_serpapi.json()
    
        if "error" in datos: return None, f"Error SerpApi: {datos['error']}"
            
        plagios_confirmados = []
        links_vistos = set()

        for item in datos.get("exact_matches", []):
            link = item.get("link", "#").lower()
            if link not in links_vistos:
                plagios_confirmados.append({
                    "titulo": item.get("title", "Coincidencia Exacta Detectada"),
                    "link": link,
                    "es_instagram": "instagram.com" in link,
                    "es_facebook": "facebook.com" in link
                })
                links_vistos.add(link)

        for item in datos.get("visual_matches", []):
            link = item.get("link", "#").lower()
            if link in links_vistos: continue
            
            thumb_url = item.get("thumbnail")
            
            if thumb_url:
                try:
                    res_thumb = requests.get(thumb_url, timeout=3)
                    if res_thumb.status_code == 200:
                        img_thumb = Image.open(io.BytesIO(res_thumb.content))
                        phash_thumb = imagehash.phash(img_thumb)
                        distancia = phash_original - phash_thumb
                        
                        if distancia <= 16:
                            plagios_confirmados.append({
                                "titulo": item.get("title", "Copia Idéntica (Verificada por pHash)"),
                                "link": link,
                                "es_instagram": "instagram.com" in link,
                                "es_facebook": "facebook.com" in link
                            })
                            links_vistos.add(link)
                except:
                    pass
            
            if len(plagios_confirmados) >= 5: break
            
        return plagios_confirmados, None
    except Exception as e:
        return None, f"Error en validación web cruzada: {str(e)}"

# ==========================================
# MOTOR 2: DOCUMENTOS (EXTRACCIÓN INTELIGENTE + GOOGLE SEARCH)
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
                    oraciones = texto.replace('\n', ' ').split('. ')
                    fragmentos_candidatos.extend(oraciones)
                    
        elif extension in ['doc', 'docx']:
            doc = docx.Document(io.BytesIO(archivo_bytes))
            for parrafo in doc.paragraphs[:20]:
                if parrafo.text:
                    oraciones = parrafo.text.replace('\n', ' ').split('. ')
                    fragmentos_candidatos.extend(oraciones)
                    
    except Exception as e:
        return None, f"Error al leer documento: {str(e)}"
        
    fragmentos_limpios = [f.strip() for f in fragmentos_candidatos if len(f.split()) > 15]
    
    if not fragmentos_limpios: 
        return [], None
        
    fragmentos_limpios.sort(key=lambda x: len(x.split()), reverse=True)
    
    mejor_fragmento = fragmentos_limpios[0]
    palabras_clave = mejor_fragmento.split()
    fragmento_clave = " ".join(palabras_clave[:25])
    
    try:
        params = { 
            "engine": "google", 
            "q": f'"{fragmento_clave}"', 
            "api_key": SERPAPI_KEY, 
            "hl": "es" 
        }
        res = requests.get("https://serpapi.com/search.json", params=params)
        datos = res.json()
        
        if "error" in datos: return None, f"Error SerpApi Text: {datos['error']}"

        resultados_limpios = []
        if "organic_results" in datos:
            for item in datos["organic_results"][:5]:
                link_encontrado = item.get("link", "#").lower()
                resultados_limpios.append({
                    "titulo": item.get("title", "Copia Textual Detectada"),
                    "link": item.get("link", "#"),
                    "es_instagram": "instagram.com" in link_encontrado,
                    "es_facebook": "facebook.com" in link_encontrado
                })
        return resultados_limpios, None
    except Exception as e:
        return None, f"Error en Motor Texto: {str(e)}"

# ==========================================
# ENRUTAMIENTOS Y LÓGICA CORE
# ==========================================

@app.route("/revisar_integridad_hash/<hash_id>", methods=["POST"])
def revisar_integridad_hash(hash_id):
    global db_proyectos
    
    # 1. Encontrar el archivo correspondiente
    proyecto = next((p for p in db_proyectos if p['hash_full'] == hash_id), None)
    if not proyecto:
        return jsonify({"error": "Proyecto no encontrado", "plagio": False}), 404

    # 2. Leer el archivo almacenado desde el disco
    ruta_guardado = os.path.join(CARPETA_BOVEDA, proyecto['nombre'])
    if not os.path.exists(ruta_guardado):
        return jsonify({"error": "El archivo físico no existe en la bóveda", "plagio": False}), 404

    try:
        with open(ruta_guardado, 'rb') as f:
            contenido_binario = f.read()
    except Exception as e:
        return jsonify({"error": str(e), "plagio": False}), 500

    nombre = proyecto['nombre']
    extension = nombre.split('.')[-1].lower()

    # 3. AISLAMIENTO TEMPORAL (Evita falso positivo local)
    db_proyectos_temporales = [p for p in db_proyectos if p['hash_full'] != hash_id]
    db_original = list(db_proyectos)
    db_proyectos.clear()
    db_proyectos.extend(db_proyectos_temporales)

    sitios_web = []
    try:
        # 4. Usar los motores definidos
        if extension in ['pdf', 'doc', 'docx']:
            sitios_web, error = buscar_documento_con_serpapi(contenido_binario, nombre)
        else:
            sitios_web, error = buscar_imagen_estricta_serpapi(contenido_binario, nombre)
            
        hay_plagio = True if sitios_web and len(sitios_web) > 0 else False
    finally:
        # 5. Restaurar la base de datos íntegra
        db_proyectos.clear()
        db_proyectos.extend(db_original)

    # 6. Actualizar el estado real en la memoria
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
    
    if abrir_boveda:
        skip_intro = True
    
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
                tipo_motor = "Motor NLP (Búsqueda Exacta) & Radar OSINT"
            else:
                try:
                    img_hash = imagehash.phash(Image.open(io.BytesIO(contenido_binario)))
                    huella_perceptual = str(img_hash)
                except:
                    pass
                
                sitios_web, error = buscar_imagen_estricta_serpapi(contenido_binario, nombre)
                tipo_motor = "Validación Cruzada (pHash) & Radar OSINT"

            hay_plagio = True if sitios_web and len(sitios_web) > 0 else False
            
            if not hay_plagio:
                try:
                    ruta_guardado = os.path.join(CARPETA_BOVEDA, nombre)
                    with open(ruta_guardado, 'wb') as f:
                        f.write(contenido_binario)
                except Exception as e:
                    print("Aviso de guardado:", e)
                
                db_proyectos.insert(0, {
                    "nombre": nombre,
                    "hash": hash_sha256[:12] + "...", 
                    "hash_full": hash_sha256, 
                    "phash": huella_perceptual, 
                    "plagio": hay_plagio,
                    "timestamp": tiempo_actual
                })
            
            return render_template('index.html', 
                                   mostrando_resultado=True, 
                                   paginas_encontradas=sitios_web, 
                                   error_api=error, 
                                   hash_resultado=hash_sha256, 
                                   nombre_archivo=nombre, 
                                   tipo_motor=tipo_motor, 
                                   timestamp=tiempo_actual, 
                                   skip_intro=True, 
                                   proyectos=db_proyectos,
                                   mostrar_boveda=False) 
            
    return render_template('index.html', 
                           mostrando_resultado=False, 
                           skip_intro=skip_intro, 
                           proyectos=db_proyectos,
                           mostrar_boveda=abrir_boveda)

if __name__ == "__main__":
    app.run(debug=True)
