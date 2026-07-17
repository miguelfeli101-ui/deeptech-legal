from flask import Flask, request, render_template, redirect, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
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
# Clave secreta necesaria para firmar las cookies de sesión de forma segura
app.secret_key = "deeptech_super_secret_key_2026" 

# ==========================================
# CONFIGURACIONES PRINCIPALES
# ==========================================
SERPAPI_KEY = "9c253e2fb00e86510296ff2a44c10d6d7e1ef197344aa602f6e06c5513b0a9ee" 

HEADERS_ESTANDAR = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

CARPETA_BOVEDA = 'boveda_local'
try:
    if not os.path.exists(CARPETA_BOVEDA):
        os.makedirs(CARPETA_BOVEDA)
except Exception as e:
    print("Aviso: No se pudo crear la carpeta principal.")

# Base de datos simulada multi-usuario
# Estructura: {'usuario': {'password': 'hash', 'proyectos': []}}
users_db = {}

# ==========================================
# MOTORES DE BÚSQUEDA
# ==========================================
def comparar_phash_local(imagen_bytes, username):
    try:
        img = Image.open(io.BytesIO(imagen_bytes))
        nuevo_phash = imagehash.phash(img)
        
        # Solo compara con los proyectos del usuario actual
        proyectos_usuario = users_db.get(username, {}).get('proyectos', [])
        
        for proyecto in proyectos_usuario:
             if 'phash' in proyecto and proyecto['phash']:
                hash_guardado = imagehash.hex_to_hash(proyecto['phash'])
                distancia = nuevo_phash - hash_guardado
                if distancia <= 2: 
                    return True
        return False
    except Exception as e:
        return False

def buscar_imagen_estricta_serpapi(imagen_bytes, nombre_archivo, username):
    if comparar_phash_local(imagen_bytes, username):
        return [{"titulo": "Registro Encontrado en Base de Datos Interna", "link": "Plataforma Local", "es_instagram": False, "es_facebook": False}], None

    try:
        img_original = Image.open(io.BytesIO(imagen_bytes))
        phash_original = imagehash.phash(img_original)
    except:
        return None, "Error decodificando imagen."

    try:
        archivos = {'reqtype': (None, 'fileupload'), 'fileToUpload': (nombre_archivo, imagen_bytes)}
        respuesta_subida = requests.post('https://catbox.moe/user/api.php', files=archivos, headers=HEADERS_ESTANDAR, timeout=15)
        url_publica = respuesta_subida.text.strip()
        if not url_publica.startswith("http"):
            return None, "No se pudo generar el enlace temporal para el radar."
    except requests.exceptions.Timeout:
         return None, "El nodo temporal tardó demasiado en responder."
    except Exception as e:
        return None, f"Error de subida al nodo: {str(e)}"

    try:
        params = {"engine": "google_lens", "url": url_publica, "api_key": SERPAPI_KEY}
        respuesta_serpapi = requests.get("https://serpapi.com/search.json", params=params, timeout=25)
        datos = respuesta_serpapi.json()
    
        if "error" in datos: return None, f"Error SerpApi: {datos['error']}"
            
        plagios_confirmados = []
        links_vistos = set()

        for item in datos.get("exact_matches", []):
            link = item.get("link", "#").lower()
            if link not in links_vistos:
                plagios_confirmados.append({"titulo": item.get("title", "Coincidencia Exacta Detectada"), "link": link, "es_instagram": "instagram.com" in link, "es_facebook": "facebook.com" in link})
                links_vistos.add(link)

        for item in datos.get("visual_matches", []):
            link = item.get("link", "#").lower()
            if link in links_vistos: continue
            thumb_url = item.get("thumbnail")
            if thumb_url:
                try:
                    res_thumb = requests.get(thumb_url, headers=HEADERS_ESTANDAR, timeout=5)
                    if res_thumb.status_code == 200:
                        img_thumb = Image.open(io.BytesIO(res_thumb.content))
                        phash_thumb = imagehash.phash(img_thumb)
                        if (phash_original - phash_thumb) <= 16:
                            plagios_confirmados.append({"titulo": item.get("title", "Copia Idéntica (Verificada por pHash)"), "link": link, "es_instagram": "instagram.com" in link, "es_facebook": "facebook.com" in link})
                            links_vistos.add(link)
                except: pass
            if len(plagios_confirmados) >= 5: break
            
        return plagios_confirmados, None
    except Exception as e:
        return None, f"Error en validación web cruzada: {str(e)}"

def buscar_documento_con_serpapi(archivo_bytes, nombre_archivo):
    fragmentos_candidatos = []
    extension = nombre_archivo.split('.')[-1].lower()
    
    try:
        if extension == 'pdf':
            lector = PyPDF2.PdfReader(io.BytesIO(archivo_bytes))
            for pagina in lector.pages[:4]:
                texto = pagina.extract_text()
                if texto: fragmentos_candidatos.extend(texto.replace('\n', ' ').split('. '))
        elif extension in ['doc', 'docx']:
            doc = docx.Document(io.BytesIO(archivo_bytes))
            for parrafo in doc.paragraphs[:20]:
                if parrafo.text: fragmentos_candidatos.extend(parrafo.text.replace('\n', ' ').split('. '))
    except Exception as e:
        return None, f"Error al leer documento: {str(e)}"
        
    fragmentos_limpios = [f.strip() for f in fragmentos_candidatos if len(f.split()) > 15]
    if not fragmentos_limpios: return [], None
        
    fragmentos_limpios.sort(key=lambda x: len(x.split()), reverse=True)
    fragmento_clave = " ".join(fragmentos_limpios[0].split()[:25])
    
    try:
        params = {"engine": "google", "q": f'"{fragmento_clave}"', "api_key": SERPAPI_KEY, "hl": "es"}
        res = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
        datos = res.json()
        
        if "error" in datos: return None, f"Error SerpApi Text: {datos['error']}"

        resultados_limpios = []
        if "organic_results" in datos:
            for item in datos["organic_results"][:5]:
                link_encontrado = item.get("link", "#").lower()
                resultados_limpios.append({"titulo": item.get("title", "Copia Textual Detectada"), "link": item.get("link", "#"), "es_instagram": "instagram.com" in link_encontrado, "es_facebook": "facebook.com" in link_encontrado})
        return resultados_limpios, None
    except Exception as e:
        return None, f"Error en Motor Texto: {str(e)}"

# ==========================================
# RUTAS DE AUTENTICACIÓN
# ==========================================
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username").lower().strip()
    password = request.form.get("password")
    
    if username in users_db and check_password_hash(users_db[username]['password'], password):
        session['username'] = username
    return redirect(url_for('index'))

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username").lower().strip()
    password = request.form.get("password")
    
    if username and username not in users_db:
        users_db[username] = {
            'password': generate_password_hash(password),
            'proyectos': []
        }
        # Crear la bóveda personal física del usuario
        user_folder = os.path.join(CARPETA_BOVEDA, username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            
        session['username'] = username
    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# ==========================================
# RUTAS DE LA APLICACIÓN
# ==========================================

@app.route("/revisar_integridad_hash/<hash_id>", methods=["POST"])
def revisar_integridad_hash(hash_id):
    if 'username' not in session: return jsonify({"error": "No autorizado"}), 401
    username = session['username']
    proyectos = users_db[username]['proyectos']
    
    proyecto = next((p for p in proyectos if p['hash_full'] == hash_id), None)
    if not proyecto: return jsonify({"error": "Proyecto no encontrado", "plagio": False}), 404

    ruta_guardado = os.path.join(CARPETA_BOVEDA, username, proyecto['nombre'])
    if not os.path.exists(ruta_guardado): return jsonify({"error": "El archivo físico no existe", "plagio": False}), 404

    try:
        with open(ruta_guardado, 'rb') as f:
            contenido_binario = f.read()
    except Exception as e:
        return jsonify({"error": str(e), "plagio": False}), 500

    nombre = proyecto['nombre']
    extension = nombre.split('.')[-1].lower()

    # AISLAMIENTO TEMPORAL (Evita falso positivo local)
    proyectos_temporales = [p for p in proyectos if p['hash_full'] != hash_id]
    users_db[username]['proyectos'] = proyectos_temporales

    sitios_web = []
    try:
        if extension in ['pdf', 'doc', 'docx']: sitios_web, error = buscar_documento_con_serpapi(contenido_binario, nombre)
        else: sitios_web, error = buscar_imagen_estricta_serpapi(contenido_binario, nombre, username)
        hay_plagio = True if sitios_web and len(sitios_web) > 0 else False
    finally:
        users_db[username]['proyectos'] = proyectos

    for p in users_db[username]['proyectos']:
        if p['hash_full'] == hash_id:
            p['plagio'] = hay_plagio
            break

    return jsonify({"plagio": hay_plagio, "sitios": sitios_web})

@app.route("/eliminar/<hash_id>")
def eliminar_proyecto(hash_id):
    if 'username' in session:
        users_db[session['username']]['proyectos'] = [p for p in users_db[session['username']]['proyectos'] if p['hash_full'] != hash_id]
    return "OK", 200

@app.route("/eliminar_multiples", methods=["POST"])
def eliminar_multiples():
    if 'username' in session:
        hashes = request.form.getlist("hashes[]")
        users_db[session['username']]['proyectos'] = [p for p in users_db[session['username']]['proyectos'] if p['hash_full'] not in hashes]
    return "OK", 200

@app.route("/renombrar", methods=["POST"])
def renombrar_proyecto():
    if 'username' in session:
        hash_id, nuevo_nombre = request.form.get("hash_id"), request.form.get("nuevo_nombre")
        for p in users_db[session['username']]['proyectos']:
            if p['hash_full'] == hash_id:
                p['nombre'] = nuevo_nombre
                break
    return "OK", 200

@app.route("/", methods=["GET", "POST"])
def index():
    logged_in = 'username' in session
    username = session.get('username')
    proyectos = users_db[username]['proyectos'] if logged_in else []
    
    skip_intro = request.args.get("skip_intro") == "true"
    abrir_boveda = request.args.get("boveda") == "true" 
    if abrir_boveda: skip_intro = True
    
    if request.method == "POST" and logged_in:
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
                try: huella_perceptual = str(imagehash.phash(Image.open(io.BytesIO(contenido_binario))))
                except: pass
                sitios_web, error = buscar_imagen_estricta_serpapi(contenido_binario, nombre, username)
                tipo_motor = "Validación Cruzada (pHash) & Radar OSINT"

            hay_plagio = True if sitios_web and len(sitios_web) > 0 else False
            
            if not hay_plagio:
                try:
                    user_folder = os.path.join(CARPETA_BOVEDA, username)
                    if not os.path.exists(user_folder): os.makedirs(user_folder)
                    ruta_guardado = os.path.join(user_folder, nombre)
                    with open(ruta_guardado, 'wb') as f: f.write(contenido_binario)
                except Exception as e: print("Aviso de guardado:", e)
                
                users_db[username]['proyectos'].insert(0, {
                    "nombre": nombre, "hash": hash_sha256[:12] + "...", 
                    "hash_full": hash_sha256, "phash": huella_perceptual, 
                    "plagio": hay_plagio, "timestamp": tiempo_actual
                })
            
            return render_template('index.html', mostrando_resultado=True, paginas_encontradas=sitios_web, error_api=error, hash_resultado=hash_sha256, nombre_archivo=nombre, tipo_motor=tipo_motor, timestamp=tiempo_actual, skip_intro=True, proyectos=users_db[username]['proyectos'], mostrar_boveda=False, logged_in=True, username=username) 
            
    return render_template('index.html', mostrando_resultado=False, skip_intro=skip_intro, proyectos=proyectos, mostrar_boveda=abrir_boveda, logged_in=logged_in, username=username)

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
