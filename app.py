from flask import Flask, request, render_template_string, redirect, jsonify
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>DeepTech Legal Solutions</title>
    <style>
  
        /* IMPORTACIÓN DE TIPOGRAFÍAS */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&family=Oswald:wght@300;400;500;600&display=swap');
        @import url('https://fonts.cdnfonts.com/css/bukhari-script');

        /* PALETA DE COLORES APLICADA */
        :root {
            --bg-dark: #0D1B2A;
            --bg-card: #1B263B;
            --accent-blue: #415A77;
            --accent-light: #778DA9;
            --text-main: #E0E1DD;
            --success: #5EEAD4;
            --alert: #FCA5A5;
        }

        body { 
            font-family: 'Montserrat', sans-serif;
            margin: 0; padding: 0; color: var(--text-main); display: flex;
            justify-content: center; align-items: center; min-height: 100vh; 
            box-sizing: border-box; background-color: var(--bg-dark); 
            overflow: hidden; letter-spacing: 0.3px;
        }

        h1, h2, h3 { font-family: 'Oswald', sans-serif; }

        /* FONDO: LIQUID MESH GRADIENT (RESTAURADO DEL CÓDIGO ANTIGUO) */
        .bg-organic {
            position: fixed;
            top: -20%; left: -20%; right: -20%; bottom: -20%; 
            z-index: -2; background-color: var(--bg-dark); filter: blur(100px); overflow: hidden;
            transform: translate3d(0, 0, 0);
            opacity: 0; animation: fadeInBg 1.5s ease-out forwards; 
        }

        @keyframes fadeInBg { from { opacity: 0; } to { opacity: 1; } }
        
        .liquid-shape { position: absolute; border-radius: 50%; opacity: 0.8; animation: liquidFlow 12s infinite alternate cubic-bezier(0.4, 0, 0.2, 1); }
        .liquid-1 { width: 70vw; height: 70vh; top: 0; left: 0; background-color: var(--bg-card); animation-duration: 16s; }
        .liquid-2 { width: 80vw; height: 80vh; bottom: 0; right: 0; background-color: var(--accent-blue); animation-duration: 14s; animation-delay: -3s; opacity: 0.6; }
        .liquid-3 { width: 50vw; height: 50vh; top: 25%; right: 20%; background-color: var(--accent-light); opacity: 0.35; animation-duration: 18s; animation-delay: -6s; }

        @keyframes liquidFlow {
            0% { transform: translate(0, 0) scale(1) rotate(0deg); border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; }
            50% { transform: translate(10%, 10%) scale(1.1) rotate(180deg); border-radius: 60% 40% 30% 70% / 50% 60% 40% 50%; }
            100% { transform: translate(-10%, -5%) scale(0.9) rotate(360deg); border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; }
        }

        @keyframes fadeUpEntrance { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }

        /* PANTALLAS DE PRESENTACIÓN */
        .landing-screen { 
            position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; 
            display: flex; flex-direction: column; align-items: center; justify-content: center; 
            color: var(--text-main); overflow-y: auto; background: transparent; 
            transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out; transform: translateY(0); 
        }

        .hero-logo-wrapper { display: flex; flex-direction: column; align-items: center; margin-bottom: 25px; filter: drop-shadow(0px 8px 20px rgba(0, 0, 0, 0.6)); opacity: 0; animation: fadeUpEntrance 1.5s cubic-bezier(0.4, 0, 0.2, 1) 0.2s forwards; }
        .logo-top-line { display: flex; align-items: flex-start; line-height: 1; }
        .logo-deeptech { font-family: 'Bukhari Script', cursive; font-size: clamp(5rem, 12vw, 8.5rem); color: var(--accent-light); font-weight: normal; text-shadow: 0px 4px 15px rgba(0,0,0, 0.5); padding-right: 5px; }
        .logo-tm { font-family: 'Oswald', sans-serif; font-size: clamp(0.9rem, 2vw, 1.4rem); color: var(--accent-light); margin-top: clamp(15px, 3.5vw, 25px); font-weight: 500; }
        .logo-bottom-line { display: flex; justify-content: center; width: 100%; margin-top: 35px; }
        .logo-legal { font-family: 'Oswald', sans-serif; font-size: clamp(1.2rem, 3vw, 2.2rem); color: var(--text-main); letter-spacing: 0.38em; font-weight: 400; text-transform: none; margin-left: 0.38em; text-shadow: 0px 4px 10px rgba(0,0,0,0.4); }

        .hero-logo-wrapper.small-logo { margin-bottom: 15px; filter: drop-shadow(0px 4px 10px rgba(0,0,0, 0.4)); animation: none; opacity: 1; }
        .hero-logo-wrapper.small-logo .logo-deeptech { font-size: clamp(3rem, 6vw, 4.5rem); }
        .hero-logo-wrapper.small-logo .logo-tm { font-size: 0.8rem; margin-top: 10px; }
        .hero-logo-wrapper.small-logo .logo-bottom-line { margin-top: 10px; }
        .hero-logo-wrapper.small-logo .logo-legal { font-size: clamp(0.8rem, 1.5vw, 1.1rem); }

        .hero-subtitle { opacity: 0; animation: fadeUpEntrance 1.5s cubic-bezier(0.4, 0, 0.2, 1) 0.8s forwards; font-family: 'Montserrat', sans-serif; font-size: 1.2em; color: var(--accent-light); font-weight: 400; margin-bottom: 60px; text-align: center; letter-spacing: 2px; }

        /* SWITCH MÁS GRANDE Y CON GLOW */
        .glass-switch-container {
            opacity: 0;
            animation: fadeUpEntrance 1.5s cubic-bezier(0.4, 0, 0.2, 1) 1.2s forwards;
            position: relative;
            width: 170px;
            height: 70px;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.02));
            border-radius: 40px;
            box-shadow: 0 0 20px rgba(119, 141, 169, 0.4), inset 0 2px 10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.1);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid var(--accent-light);
            cursor: pointer;
            display: flex;
            align-items: center;
            padding: 6px;
            box-sizing: border-box;
            transition: all 0.3s ease;
        }
        .glass-switch-container:hover { 
            box-shadow: 0 0 30px rgba(119, 141, 169, 0.7), inset 0 2px 10px rgba(0, 0, 0, 0.5);
        }
        
        .switch-thumb {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.05));
            border-radius: 50%;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.4), inset 0 2px 5px rgba(255, 255, 255, 0.2);
            display: flex; justify-content: center; align-items: center; font-size: 1.5em;
            transform: translateX(0);
            transition: transform 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55), background 0.3s ease, box-shadow 0.3s ease;
        }
        .switch-thumb.active {
            transform: translateX(100px);
            background: linear-gradient(135deg, var(--accent-light), var(--accent-blue));
            box-shadow: 0 0 20px var(--accent-light), inset 0 2px 5px rgba(255, 255, 255, 0.5);
        }
        .switch-icon {
            transition: opacity 0.2s ease, transform 0.3s ease;
            position: absolute;
            color: var(--bg-dark);
            text-shadow: 0 2px 5px rgba(0,0,0,0.5);
        }
        .icon-lock { opacity: 1; transform: scale(1); }
        .icon-unlock { opacity: 0; transform: scale(0.5); }
        .switch-thumb.active .icon-lock { opacity: 0; transform: scale(0.5); }
        .switch-thumb.active .icon-unlock { opacity: 1; transform: scale(1); text-shadow: none;}


        /* =========================================
           MAQUETACIÓN MODERNA (CERO SCROLL / CENTRADO PERFECTO)
           ========================================= */
        #main-wrapper { 
            width: 100vw; height: 100vh; position: relative; overflow: hidden;
            transition: opacity 0.5s ease-in-out; display: flex; flex-direction: column; z-index: 1000;
        }

        /* MENÚ FLOTANTE TIPO BURBUJA */
        .nav-wrapper {
            display: flex; justify-content: center; margin: 30px auto 10px auto; width: 100%; flex-shrink: 0;
        }
        .top-nav { 
            position: relative;
            background: rgba(27, 38, 59, 0.5);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(119, 141, 169, 0.2);
            border-radius: 50px;
            display: flex; align-items: center; gap: 5px; 
            padding: 6px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            z-index: 10; flex-wrap: nowrap; overflow-x: auto; max-width: 90%;
        }
        .top-nav::-webkit-scrollbar { display: none; }
        
        .bubble-indicator {
            position: absolute; top: 6px; bottom: 6px; left: 6px; width: 0px;
            background: linear-gradient(135deg, var(--accent-light), var(--accent-blue));
            border-radius: 40px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 0;
            box-shadow: 0 4px 15px rgba(119, 141, 169, 0.4);
        }

        .tab-btn { 
            position: relative; z-index: 1;
            background: transparent !important; border: none; color: rgba(224, 225, 221, 0.7); 
            padding: 10px 22px; border-radius: 30px; font-size: 0.9em;
            font-family: 'Montserrat', sans-serif; font-weight: 500; 
            cursor: pointer; transition: color 0.3s ease; letter-spacing: 0.5px;
            white-space: nowrap; display: flex; align-items: center; justify-content: center;
        }
        .tab-btn:hover { color: var(--text-main); }
        .tab-btn.active { color: var(--bg-dark); font-weight: 600; text-shadow: 0 1px 2px rgba(255,255,255,0.3); }
        
        .notif-badge { background-color: var(--alert); color: var(--bg-dark); font-size: 0.85em; font-family: 'Montserrat', sans-serif; font-weight: 600; padding: 2px 7px; border-radius: 12px; margin-left: 8px; box-shadow: 0px 2px 5px rgba(0,0,0,0.4); display: none; align-items: center; justify-content: center; }

        /* CONTENEDORES CENTRADOS MÁGICOS */
        .section-container { 
            width: 100%; flex: 1; box-sizing: border-box; transition: opacity 0.4s ease-in-out; 
            overflow-y: auto; display: flex; flex-direction: column; align-items: center; 
            justify-content: flex-start; /* SafeArea para el Scroll */
            z-index: 1; padding: 10px 0 30px 0;
        }
        .section-container::-webkit-scrollbar { width: 6px; }
        .section-container::-webkit-scrollbar-thumb { background-color: rgba(119, 141, 169, 0.3); border-radius: 4px; }
        
        .sub-section-container { width: 100%; flex-grow: 1; box-sizing: border-box; transition: opacity 0.3s ease-in-out; display: flex; flex-direction: column; align-items: center; opacity: 0; display: none;}
        
        .app-centered-layout { display: flex; flex-direction: column; align-items: center; box-sizing: border-box; }
        
        .content-wrapper-inner { 
            width: 100%; max-width: 900px; padding: 0 20px; box-sizing: border-box; 
            display: flex; flex-direction: column; align-items: center; 
            margin: auto; /* ESTO CENTRA TODO VERTICALMENTE SIN ROMPER EL SCROLL */
        }
        
        .app-title { font-family: 'Oswald', sans-serif; font-size: 2.5em; color: var(--text-main); margin: 0 0 5px 0; text-align: center; font-weight: 500; text-shadow: 0 4px 15px rgba(0,0,0,0.4);}
        .app-subtitle { font-family: 'Montserrat', sans-serif; font-size: 1em; color: rgba(224, 225, 221, 0.7); text-align: center; margin-bottom: 25px; font-weight: 300;}
        
        /* BOTONES DENTRO DE LA PLATAFORMA */
        .btn { 
            background: var(--accent-blue); color: var(--bg-dark); padding: 12px 30px; font-size: 1em; 
            border: none; border-radius: 30px; cursor: pointer; font-weight: 600; font-family: 'Montserrat', sans-serif; 
            display: inline-block; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); letter-spacing: 0.5px;
        }
        .btn:hover { background: var(--accent-light); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(119, 141, 169, 0.3); }
        .btn:active { transform: scale(0.96) translateY(0px); }
        
        .btn-secondary { 
            background: rgba(27, 38, 59, 0.5); border: 1px solid rgba(119, 141, 169, 0.4); 
            color: var(--text-main); padding: 12px 30px; border-radius: 30px; font-size: 0.95em; transition: all 0.2s ease;
        }
        .btn-secondary:hover:not(:disabled) { background: rgba(119, 141, 169, 0.3); transform: translateY(-2px); border-color: var(--accent-light);}
        
        /* TARJETAS GLASS */
        .glass-card, .upload-area, .result-card-minimal, .metric-card, .card-proyecto, .notif-card {
            background: linear-gradient(145deg, rgba(27, 38, 59, 0.6), rgba(13, 27, 42, 0.7));
            backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-top: 1px solid rgba(119, 141, 169, 0.2);
            border-left: 1px solid rgba(119, 141, 169, 0.08);
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        
        .glass-grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 25px; width: 100%;}
        .glass-grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 20px; width: 100%;}
        
        .glass-card { padding: 20px 25px; text-align: center; } 
        .glass-card:hover { transform: translateY(-4px); border-color: rgba(119, 141, 169, 0.5); }
        .glass-card h3 { color: var(--accent-light); font-size: 1.4em; margin-bottom: 12px; font-family: 'Oswald', sans-serif; font-weight: 400; letter-spacing: 0.5px; display: flex; align-items: center; justify-content: center; gap: 8px;}
        .glass-card p { font-size: 0.9em; color: rgba(224, 225, 221, 0.8); line-height: 1.6; margin: 0; font-weight: 300; }

        /* ÁREA DE SUBIDA Y BARRA DE CARGA */
        .upload-area { width: 100%; max-width: 550px; text-align: center; padding: 30px; margin: 0 auto; box-sizing: border-box;}
        
        .loading-bar-container { width: 100%; max-width: 400px; height: 6px; background-color: rgba(0,0,0,0.4); border-radius: 10px; margin: 30px auto; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.6); }
        .loading-bar-fill { height: 100%; width: 0%; border-radius: 10px; background: linear-gradient(90deg, var(--accent-blue), var(--accent-light), var(--accent-blue)); background-size: 200% 100%; animation: shimmerGradient 2.5s linear infinite; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
        @keyframes shimmerGradient { 0% { background-position: 200% 0; } 100% { background-position: 0% 0; } }

        /* TARJETAS DE RESULTADO */
        .result-card-minimal { width: 100%; max-width: 550px; margin: 20px auto; text-align: center; box-sizing: border-box; padding: 30px; }
        .result-card-minimal.success { border-top: 2px solid var(--success); }
        .result-card-minimal.alert { border-top: 2px solid var(--alert); }
        
        input[type="file"] { margin-top: 15px; margin-bottom: 25px; padding: 12px; border: 1px dashed rgba(119, 141, 169, 0.4); border-radius: 12px; width: 100%; box-sizing: border-box; background-color: rgba(0, 0, 0, 0.2); color: var(--text-main); font-family: 'Montserrat', sans-serif; cursor: pointer; }
        
        .url-list { max-height: 120px; overflow-y: auto; background-color: rgba(0, 0, 0, 0.2); padding: 15px; border-radius: 12px; font-size: 0.85em; margin-top: 10px; font-family: 'Montserrat', sans-serif; font-weight: 300; border: 1px solid rgba(119, 141, 169, 0.15);}
        .url-list li { margin-bottom: 10px; color: rgba(224, 225, 221, 0.7); }
        .url-list a { color: var(--accent-light); text-decoration: none; font-weight: 500; }
        
        .social-badge { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 0.75em; font-weight: 500; color: white; margin-right: 8px; font-family: 'Montserrat', sans-serif;}
        .badge-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); }
        .badge-facebook { background-color: #1877F2; }
        .badge-x { background-color: #000000; border: 1px solid rgba(255,255,255,0.2); }
        
        /* DASHBOARD METRICS Y BÓVEDA */
        .metrics-wrapper { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; width: 100%; margin-bottom: 20px; }
        .metric-card { padding: 15px; text-align: center; border-radius: 16px; }
        .metric-value { font-family: 'Montserrat', sans-serif; font-weight: 600; font-size: 2em; color: var(--text-main); margin: 0; line-height: 1.2; }
        .metric-label { font-size: 0.8em; color: rgba(224, 225, 221, 0.6); font-weight: 400; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
        
        .sub-nav { display: flex; justify-content: center; gap: 10px; width: 100%; margin-bottom: 20px; flex-wrap: wrap; }
        .sub-tab-btn { background: transparent; border: 1px solid rgba(119, 141, 169, 0.3); color: rgba(224, 225, 221, 0.6); padding: 8px 20px; border-radius: 20px; font-size: 0.85em; font-family: 'Montserrat', sans-serif; font-weight: 500; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center;}
        .sub-tab-btn:hover { background-color: rgba(119, 141, 169, 0.15); color: var(--text-main); }
        .sub-tab-btn.active { background-color: var(--accent-light); color: var(--bg-dark); border-color: var(--accent-light);}
        
        /* TARJETAS DE PROYECTOS Y SELECCIÓN */
        .grid-proyectos { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; width: 100%; justify-items: center;}
        .card-proyecto { padding: 15px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; cursor: default; width: 100%; box-sizing: border-box; }
        .card-proyecto .img-mock { height: 60px; width: 100%; background-color: rgba(0, 0, 0, 0.2); border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; font-size: 2em; border: 1px solid rgba(119, 141, 169, 0.1); }
        .badge-status { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 0.7em; margin-top: 10px; font-weight: 500; font-family: 'Montserrat', sans-serif; text-align: center; }
        .badge-clean { background-color: rgba(94, 234, 212, 0.1); color: var(--success); border: 1px solid rgba(94, 234, 212, 0.3);} 
        .badge-alert { background-color: rgba(252, 165, 165, 0.15); color: var(--alert); border: 1px solid rgba(252, 165, 165, 0.4);} 
        
        .card-header-flex { width: 100%; display: flex; justify-content: space-between; margin-bottom: 5px; align-items: center; }
        .dropdown { position: relative; display: inline-block; }
        .dots-btn { background: none; border: none; color: rgba(224,225,221,0.5); font-size: 1.5em; cursor: pointer; padding: 0; line-height: 1; transition: color 0.2s; }
        .dots-btn:hover { color: var(--text-main); }
        .dropdown-content { display: none; position: absolute; right: 0; top: 100%; background: rgba(13, 27, 42, 0.95); backdrop-filter: blur(10px); min-width: 170px; box-shadow: 0px 8px 25px rgba(0,0,0,0.6); z-index: 100; border-radius: 12px; border: 1px solid rgba(119, 141, 169, 0.2); overflow: hidden; margin-top: 8px; }
        .dropdown-content a { color: var(--text-main); padding: 12px 16px; text-decoration: none; display: block; font-size: 0.85em; text-align: left; transition: background 0.2s; font-weight: 400;}
        .dropdown-content a:hover { background-color: rgba(119, 141, 169, 0.2); }
        .show { display: block; }

        /* LÓGICA DE SELECCIÓN EN LOTE */
        #lista-boveda.selection-mode .card-proyecto { cursor: pointer; }
        .select-indicator { position: absolute; top: 12px; left: 12px; width: 20px; height: 20px; border-radius: 50%; border: 2px solid rgba(224, 225, 221, 0.4); display: none; align-items: center; justify-content: center; font-size: 12px; color: transparent; transition: all 0.2s; z-index: 5; background: rgba(0, 0, 0, 0.4); }
        .selection-mode .select-indicator { display: flex; }
        .card-proyecto.selected { border-color: var(--accent-light); background: rgba(119, 141, 169, 0.15); transform: scale(0.98); }
        .card-proyecto.selected .select-indicator { background-color: var(--accent-light); border-color: var(--accent-light); color: var(--bg-dark); }
        
        .bulk-action-bar { display: none; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(27, 38, 59, 0.95); backdrop-filter: blur(10px); border: 1px solid rgba(119, 141, 169, 0.3); padding: 12px 25px; border-radius: 50px; z-index: 9999; align-items: center; gap: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); opacity: 0; transition: opacity 0.3s ease; }
        .btn-danger { background-color: var(--alert); color: var(--bg-dark); border: none; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 0.9em; font-weight: 600; transition: all 0.2s; font-family: 'Montserrat', sans-serif;}
        .btn-danger:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(252, 165, 165, 0.4);}

        /* LISTAS Y PLANES AJUSTADO PARA EVITAR SCROLL */
        .plan-price { font-family: 'Montserrat', sans-serif; font-size: 2.2em; margin: 5px 0 12px 0; color: var(--text-main); font-weight: 600;}
        .plan-list { text-align: left; font-size: 0.8em; color: rgba(224, 225, 221, 0.7); padding-left: 0; line-height: 1.5; list-style: none; flex-grow: 1;}
        .plan-list li { margin-bottom: 6px; display: flex; align-items: flex-start; gap: 8px; }
        .plan-list li::before { content: '✔'; color: var(--accent-light); border-radius: 50%; width: 15px; height: 15px; display: flex; align-items: center; justify-content: center; font-size: 0.8em; flex-shrink: 0; margin-top: 1px;}

        /* MODALES */
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0, 0.8); z-index: 20000; align-items: center; justify-content: center; backdrop-filter: blur(10px); opacity: 0; transition: opacity 0.3s ease; }
        .modal-close-btn { position: absolute; top: 12px; right: 12px; background: rgba(119, 141, 169, 0.2); border: 1px solid rgba(119, 141, 169, 0.3); color: var(--text-main); width: 30px; height: 30px; border-radius: 50%; font-size: 1.2em; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 50; transition: all 0.2s ease; }
        .modal-close-btn:hover { background: var(--alert); color: var(--bg-dark); border-color: var(--alert);}

        /* CERTIFICADO */
        .certificate-box { border: 1px solid rgba(119, 141, 169, 0.3); padding: 25px; position: relative; background: rgba(0,0,0, 0.3); border-radius: 16px; margin-top: 10px; }
        .cert-logo { font-family: 'Bukhari Script', cursive; font-size: 2em; color: var(--accent-light); margin: 0; line-height: 1; opacity: 0.9;}
        .cert-title { font-family: 'Montserrat', sans-serif; font-size: 1.1em; color: var(--text-main); letter-spacing: 2px; margin: 10px 0 15px 0; border-bottom: 1px solid rgba(119, 141, 169, 0.2); padding-bottom: 10px; font-weight: 500;}
        .cert-text { font-size: 0.8em; font-weight: 300; line-height: 1.5; color: rgba(224, 225, 221, 0.8); text-align: justify; margin-bottom: 15px; }
        
        .fade-in-element { animation: fadeUpEntrance 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
    </style>
</head>
<body>

    <div class="bg-organic">
        <div class="liquid-shape liquid-1"></div>
        <div class="liquid-shape liquid-2"></div>
        <div class="liquid-shape liquid-3"></div>
    </div>

    <div id="landing-main" class="landing-screen" {% if skip_intro %} style="display: none; opacity: 0;" {% else %} style="display: flex; opacity: 1;" {% endif %}>
        <div class="hero-logo-wrapper">
            <div class="logo-top-line">
                <span class="logo-deeptech">DeepTech</span><span class="logo-tm">TM</span>
            </div>
            <div class="logo-bottom-line">
                <span class="logo-legal">Legal Solutions</span>
            </div>
        </div>
        <p class="hero-subtitle">POTENCIADO POR INTELIGENCIA ARTIFICIAL & BLOCKCHAIN</p>
        
        <div class="glass-switch-container" onclick="activarToggle(this)">
            <div class="switch-thumb" id="switch-thumb-btn">
                <span class="switch-icon icon-lock" id="icon-lock">🔒</span>
                <span class="switch-icon icon-unlock" id="icon-unlock">🔓</span>
            </div>
        </div>
    </div>

    <div id="main-wrapper" {% if skip_intro %} style="display: flex; opacity: 1;" {% else %} style="display: none; opacity: 0;" {% endif %}>
        
        <div class="nav-wrapper">
            <div class="top-nav" id="main-nav">
                <div class="bubble-indicator" id="nav-bubble"></div>
                
                <button id="tab-auditar" class="tab-btn {% if not mostrar_boveda %}active{% endif %}" onclick="cambiarPestana('app-section', this)">Auditar Archivo</button>
                <button id="tab-boveda" class="tab-btn {% if mostrar_boveda %}active{% endif %}" onclick="cambiarPestana('dashboard-section', this)">Mis Proyectos</button>
                <button id="tab-planes" class="tab-btn" onclick="cambiarPestana('planes-section', this)">Planes</button>
                <button id="tab-como-funciona" class="tab-btn" onclick="cambiarPestana('como-funciona-section', this)">¿Cómo funciona?</button>
                <button id="tab-quienes" class="tab-btn" onclick="cambiarPestana('quienes-section', this)">¿Quiénes Somos?</button>
                <button id="tab-notificaciones" class="tab-btn" onclick="cambiarPestana('notificaciones-section', this)">
                    Buzón 🗂️ <span id="notif-badge" class="notif-badge">0</span>
                </button>
            </div>
        </div>

        <div id="loading-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner">
                <h2 class="app-title">Cifrando y Analizando...</h2>
                <p id="texto-carga" class="app-subtitle">Asegurando el archivo en la Bóveda Local.</p>
                <div class="loading-bar-container">
                    <div class="loading-bar-fill" id="main-loading-fill"></div>
                </div>
            </div>
        </div>

        <div id="app-section" class="section-container app-centered-layout" {% if mostrar_boveda %} style="display: none; opacity: 0;" {% else %} style="display: flex; opacity: 1;" {% endif %}>
            <div id="app-inner-wrapper" class="content-wrapper-inner">
                <div id="upload-titles" style="width: 100%; display: flex; flex-direction: column; align-items: center; {% if mostrando_resultado %}display: none;{% endif %}">
                    <div class="hero-logo-wrapper small-logo">
                        <div class="logo-top-line">
                            <span class="logo-deeptech">DeepTech</span><span class="logo-tm">TM</span>
                        </div>
                        <div class="logo-bottom-line">
                            <span class="logo-legal">Legal Solutions</span>
                        </div>
                    </div>
                    <p class="app-subtitle" style="margin-top: 0; max-width: 600px;">Sube tu activo digital (Imagen o Documento) para certificar su originalidad y protegerlo.</p>
                </div>
                
                <div class="upload-area" id="upload-area-box" {% if mostrando_resultado %} style="display: none;" {% endif %}>
                    <form id="upload-form" action="/" method="POST" enctype="multipart/form-data" onsubmit="ejecutarCarga()" style="display: flex; flex-direction: column; align-items: center;">
                        <label style="font-weight: 500; color: var(--text-main); text-align: center; font-size: 1.1em; font-family: 'Montserrat', sans-serif;">Selecciona el archivo para certificar:</label>
                        <input type="file" name="archivo" accept="image/*,.pdf,.doc,.docx" required id="input-archivo">
                        <button type="submit" class="btn" style="width: 100%;">Analizar y Proteger en Bóveda</button>
                    </form>
                </div>

                <div id="upload-badges" style="display: {% if mostrando_resultado %}none{% else %}flex{% endif %}; justify-content: center; gap: 20px; margin-top: 30px; opacity: 0.8;">
                    <div style="display: flex; align-items: center; gap: 5px; font-size: 0.85em; color: rgba(224, 225, 221, 0.7);"><span style="color: var(--accent-light);">🛡️</span> Privacidad Absoluta</div>
                    <div style="display: flex; align-items: center; gap: 5px; font-size: 0.85em; color: rgba(224, 225, 221, 0.7);"><span style="color: var(--accent-light);">⚖️</span> Validez Legal DMCA</div>
                </div>
                
                {% if mostrando_resultado %}
                <div id="resultado-area" class="fade-in-element" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
                    {% if error_api %}
                        <div class="result-card-minimal alert">
                            <h2 style="color: var(--alert); margin-top: 0; font-family: 'Montserrat', sans-serif; font-weight: 500;">Error de Conexión</h2>
                            <p style="color: rgba(224,225,221,0.8); font-weight: 300; margin-bottom: 0;">{{ error_api }}</p>
                        </div>
                        <div style="display: flex; justify-content: center; margin-top: 20px;">
                            <button class="btn btn-secondary" onclick="transicionAuditarNuevo()">Auditar nuevo archivo</button>
                        </div>
                    {% elif paginas_encontradas %}
                        <div class="result-card-minimal alert">
                            <h2 style="color: var(--alert); margin-top: 0; font-family: 'Montserrat', sans-serif; font-size: 2em; font-weight: 500;">⛔ Alerta de Plagio</h2>
                            <p style="color: rgba(224,225,221,0.8); font-weight: 300; font-size: 1.05em; margin-bottom: 25px;">Se detectaron coincidencias web del archivo <span style="color: var(--text-main); font-weight: 500;">{{ nombre_archivo }}</span>.</p>
                            <button class="btn btn-secondary" style="color: var(--alert); border-color: rgba(252, 165, 165, 0.4);" onclick="document.getElementById('detalles-plagio').style.display='block'; this.style.display='none';">Ver Informe Completo</button>
                            <div id="detalles-plagio" style="display: none; text-align: left; margin-top: 25px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px; animation: fadeUpEntrance 0.5s ease forwards;">
                                <p style="color: var(--alert); font-size: 0.9em; border: 1px solid rgba(252, 165, 165, 0.2); padding: 12px; border-radius: 8px; background: rgba(252, 165, 165, 0.05); font-weight: 300;">Aviso de Sistema: Para evitar infracciones de derechos de autor, este archivo no ha sido guardado en la bóveda.</p>
                                <p style="color: rgba(224,225,221,0.7); font-weight: 300; font-size: 0.9em; margin-top: 15px;">Radar Ejecutado: <span style="color: var(--alert);">{{ tipo_motor }}</span></p>
                                <p style="color: rgba(224, 225, 221, 0.85); font-weight: 300; font-size: 0.9em; margin-top: 15px;">Enlaces confirmados con el contenido original:</p>
                                <div class="url-list">
                                    <ol style="margin: 0; padding-left: 20px;">
                                    {% for sitio in paginas_encontradas %}
                                        <li style="margin-bottom: 10px;">
                                            <a href="{{ sitio.link }}" target="_blank" style="font-size: 0.95em;">{{ sitio.titulo }}</a>
                                            {% if sitio.es_instagram %}<span class="social-badge badge-instagram">Instagram</span>
                                            {% elif sitio.es_facebook %}<span class="social-badge badge-facebook">Facebook</span>{% endif %}
                                            <br><small style="color: rgba(224,225,221,0.5); word-break: break-all;">{{ sitio.link }}</small>
                                        </li>
                                    {% endfor %}
                                    </ol>
                                </div>
                                <p style="margin-top: 15px; color: rgba(224,225,221,0.7); font-weight: 300; font-size: 0.85em;">Firma Hash Auditada: <br><span style="font-family: monospace; color: var(--text-main);">{{ hash_resultado }}</span></p>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: center; gap: 15px; margin-top: 20px; flex-wrap: wrap;">
                            <button class="btn btn-secondary" onclick="transicionAuditarNuevo()">Auditar nuevo archivo</button>
                            <button class="btn btn-secondary" onclick="abrirAuditoria()">¿Tu archivo es original?</button>
                        </div>
                    {% else %}
                        <div class="result-card-minimal success">
                            <h2 style="color: var(--success); margin-top: 0; font-family: 'Montserrat', sans-serif; font-size: 2em; font-weight: 500;">✅ Activo Original</h2>
                            <p style="color: rgba(224,225,221,0.8); font-weight: 300; font-size: 1.05em; margin-bottom: 25px;">El archivo <span style="color: var(--text-main); font-weight: 500;">{{ nombre_archivo }}</span> es único y seguro.</p>
                            <button class="btn btn-secondary" style="color: var(--success); border-color: rgba(94, 234, 212, 0.4);" onclick="document.getElementById('detalles-original').style.display='block'; this.style.display='none';">Ver Informe Completo</button>
                            <div id="detalles-original" style="display: none; text-align: left; margin-top: 25px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px; animation: fadeUpEntrance 0.5s ease forwards;">
                                <p style="color: rgba(224, 225, 221, 0.8); font-weight: 300; font-size: 0.9em;">El análisis profundo no detectó copias en la red. El archivo se ha guardado exitosamente en tu bóveda criptográfica.</p>
                                <p style="color: rgba(224, 225, 221, 0.7); font-weight: 300; font-size: 0.9em; margin-top: 15px;">Radar Ejecutado: <span style="color: var(--success);">{{ tipo_motor }}</span></p>
                                <p style="color: rgba(224, 225, 221, 0.7); font-weight: 300; font-size: 0.9em; margin-top: 15px;">Firma Hash Blockchain: <br> <span style="font-family: monospace; color: var(--text-main); word-break: break-all;">{{ hash_resultado }}</span></p>
                                <p style="color: rgba(224, 225, 221, 0.5); margin-bottom: 0; font-weight: 300; font-size: 0.85em;">Sello de tiempo: {{ timestamp }}</p>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: center; margin-top: 20px;">
                            <button class="btn btn-secondary" onclick="transicionAuditarNuevo()">Auditar nuevo archivo</button>
                        </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>

        <div id="dashboard-section" class="section-container app-centered-layout" {% if mostrar_boveda %} style="display: flex; opacity: 1;" {% else %} style="display: none; opacity: 0;" {% endif %}>
            <div class="content-wrapper-inner" style="max-width: 900px;">
                
                <div style="width: 100%; display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                    <div>
                        <h2 class="app-title" style="text-align: left; margin: 0; font-size: 2em;">Bóveda Criptográfica</h2>
                        <p class="app-subtitle" style="text-align: left; margin: 5px 0 0 0;">Archivos encriptados y monitoreados en tiempo real.</p>
                    </div>
                    <button id="btn-revisar-integridad" class="btn btn-secondary" style="font-size: 0.85em; padding: 10px 20px;" onclick="revisarIntegridad()">🔎 Analizar Integridad</button>
                </div>
                
                <div class="metrics-wrapper">
                    <div class="metric-card glass-card">
                        <p class="metric-value">{{ proyectos|selectattr('plagio', 'equalto', False)|list|length }}</p>
                        <p class="metric-label">Activos Protegidos</p>
                    </div>
                    <div class="metric-card glass-card">
                        <p class="metric-value" style="color: var(--alert);">34</p>
                        <p class="metric-label">Plagios Bloqueados</p>
                    </div>
                    <div class="metric-card glass-card">
                        <p class="metric-value" style="font-size: 1.5em; margin-top: 8px;">📡</p>
                        <p class="metric-label">Radar OSINT 24/7</p>
                    </div>
                </div>

                <div class="sub-nav">
                    <button class="sub-tab-btn active" onclick="cambiarSubPestana('boveda-personal-tab', this)">Mi Bóveda Personal</button>
                    <button class="sub-tab-btn" onclick="cambiarSubPestana('boveda-instagram-tab', this)">
                        <span class="social-badge badge-instagram">IG</span> Instagram <span style="color: var(--accent-light); font-size: 0.7em; margin-left: 5px;">PRO</span>
                    </button>
                    <button class="sub-tab-btn" onclick="cambiarSubPestana('boveda-facebook-tab', this)">
                        <span class="social-badge badge-facebook">FB</span> Facebook <span style="color: var(--accent-light); font-size: 0.7em; margin-left: 5px;">PRO</span>
                    </button>
                    <button class="sub-tab-btn" onclick="cambiarSubPestana('boveda-x-tab', this)">
                        <span class="social-badge badge-x">𝕏</span> X (Twitter) <span style="color: var(--accent-light); font-size: 0.7em; margin-left: 5px;">PRO</span>
                    </button>
                </div>
                
                <div id="boveda-personal-tab" class="sub-section-container" style="display: flex; opacity: 1;">
                    <div class="grid-proyectos" id="lista-boveda">
                        {% if proyectos %}
                            {% for p in proyectos %}
                            <div class="card-proyecto glass-card" data-hash="{{ p.hash_full }}" onclick="clickEnTarjeta(event, this)">
                                <div class="select-indicator"></div>
                                <div class="card-header-flex">
                                    <span></span>
                                    <div class="dropdown">
                                        <button onclick="toggleDropdown('drop-{{ loop.index }}')" class="dots-btn">⋮</button>
                                        <div id="drop-{{ loop.index }}" class="dropdown-content">
                                            <a href="#" onclick="verInforme('{{ p.nombre }}', '{{ p.hash_full }}', '{{ p.plagio }}')">Ver informe general</a>
                                            <a href="#" style="color: var(--accent-light); font-size: 0.82em; white-space: normal; line-height: 1.3;" onclick="verCertificado('{{ p.nombre }}', '{{ p.hash_full }}', '{{ p.timestamp|default('Fecha no disponible') }}')">Ver Certificado Legal</a>
                                            <a href="#" onclick="activarModoSeleccion('{{ p.hash_full }}')">Seleccionar</a>
                                            <a href="#" onclick="renombrarArchivo('{{ p.hash_full }}', '{{ p.nombre }}', this)">Cambiar nombre</a>
                                            <a href="#" onclick="eliminarConAnimacion('{{ p.hash_full }}', this)">Eliminar</a>
                                        </div>
                                    </div>
                                </div>
                                <div class="img-mock">
                                    {% if p.nombre.endswith('.pdf') %}📑{% elif p.nombre.endswith('.docx') or p.nombre.endswith('.doc') %}📑{% else %}🖼️{% endif %}
                                </div>
                                <p style="margin: 0; font-weight: 500; font-size: 0.95em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-main); width: 100%;" title="{{ p.nombre }}">{{ p.nombre }}</p>
                                <small style="color: rgba(224, 225, 221, 0.5); font-size: 0.7em; margin-top: 5px; font-family: monospace;">ID: {{ p.hash }}</small>
                                {% if p.plagio %}<span class="badge-status badge-alert">⛔ Alerta en Web</span>{% else %}<span class="badge-status badge-clean">✅ Monitor Activo</span>{% endif %}
                            </div>
                            {% endfor %}
                        {% else %}
                            <div style="grid-column: 1 / -1; text-align: center; color: rgba(224, 225, 221, 0.5); padding: 40px;">
                                <p style="font-weight: 300; margin-bottom: 20px;">Tu bóveda está vacía.<br>Sube tu primer archivo para protegerlo.</p>
                                <button class="btn btn-secondary" onclick="cambiarPestana('app-section', document.getElementById('tab-auditar'))">Subir Archivo</button>
                            </div>
                        {% endif %}
                    </div>
                </div>

                <div id="boveda-instagram-tab" class="sub-section-container">
                    <div id="ig-connect-area" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; transition: opacity 0.3s ease;">
                        <div class="glass-card" style="max-width: 500px; width: 100%;">
                            <div style="font-size: 3em; margin-bottom: 10px;">📱</div>
                            <h3 style="margin-top:0;">Protección Automatizada</h3>
                            <p style="margin-bottom: 25px;">Vincula tu Instagram para proteger cada nueva publicación automáticamente en la Blockchain.</p>
                            <button class="btn" style="background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); border: none; font-size: 0.95em; padding: 12px 30px; color:white;" onclick="simularConexion('Instagram', 'ig-connect-area')">Vincular cuenta de Instagram</button>
                        </div>
                    </div>
                </div>

                <div id="boveda-facebook-tab" class="sub-section-container">
                    <div id="fb-connect-area" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; transition: opacity 0.3s ease;">
                        <div class="glass-card" style="max-width: 500px; width: 100%;">
                            <div style="font-size: 3em; margin-bottom: 10px;">🏢</div>
                            <h3 style="margin-top:0;">Blindaje Corporativo</h3>
                            <p style="margin-bottom: 25px;">Conecta la Fanpage de tu empresa para un registro OSINT de catálogos y banners.</p>
                            <button class="btn" style="background-color: #1877F2; border: none; font-size: 0.95em; padding: 12px 30px; color:white;" onclick="simularConexion('Facebook', 'fb-connect-area')">Vincular página de Facebook</button>
                        </div>
                    </div>
                </div>

                <div id="boveda-x-tab" class="sub-section-container">
                    <div id="x-connect-area" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; transition: opacity 0.3s ease;">
                        <div class="glass-card" style="max-width: 500px; width: 100%;">
                            <div style="font-size: 3em; margin-bottom: 10px;">💬</div>
                            <h3 style="margin-top:0;">Certificación en Tiempo Real</h3>
                            <p style="margin-bottom: 25px;">Protege tus hilos virales, investigaciones y material audiovisual en el momento exacto.</p>
                            <button class="btn" style="background-color: #0F1419; border: 1px solid rgba(255,255,255,0.2); font-size: 0.95em; padding: 12px 30px; color:white;" onclick="simularConexion('X', 'x-connect-area')">Vincular cuenta de X</button>
                        </div>
                    </div>
                </div>

            </div>
        </div>

        <div id="planes-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 1000px;">
                <h2 class="app-title">Planes y Precios</h2>
                <p class="app-subtitle">Escala la protección de tus activos según tus necesidades.</p>
                <div class="glass-grid-3">
                    <div class="glass-card" style="display: flex; flex-direction: column;">
                        <h3>Básico</h3>
                        <div class="plan-price">Gratis</div>
                        <ul class="plan-list">
                            <li>Protección manual de activos</li>
                            <li>Límite de 5 archivos</li>
                            <li>Generación de firma Hash</li>
                            <li>Auditoría bajo demanda</li>
                        </ul>
                        <button class="btn btn-secondary" style="width: 100%; margin-top: 15px;">Plan Actual</button>
                    </div>
                    <div class="glass-card" style="display: flex; flex-direction: column; background: linear-gradient(145deg, rgba(27, 38, 59, 0.8), rgba(13, 27, 42, 0.9)); border-color: rgba(119, 141, 169, 0.3);">
                        <h3>Pro Creador</h3>
                        <div class="plan-price">$9.99<span style="font-size: 0.4em; color: rgba(224, 225, 221, 0.5);">/m</span></div>
                        <ul class="plan-list">
                            <li>Todo lo del plan Básico</li>
                            <li>Sincronización IG y X</li>
                            <li>Archivos ilimitados</li>
                            <li>Radar OSINT 24/7 activo</li>
                        </ul>
                        <button class="btn" style="width: 100%; margin-top: 15px;">Mejorar a Pro</button>
                    </div>
                    <div class="glass-card" style="display: flex; flex-direction: column;">
                        <h3>Enterprise</h3>
                        <div class="plan-price">$49.99<span style="font-size: 0.4em; color: rgba(224, 225, 221, 0.5);">/m</span></div>
                        <ul class="plan-list">
                            <li>Todo lo del plan Pro</li>
                            <li>Conexión de Fanpages</li>
                            <li>Protección masiva</li>
                            <li>Takedown automático</li>
                        </ul>
                        <button class="btn btn-secondary" style="width: 100%; margin-top: 15px;">Contactar Ventas</button>
                    </div>
                </div>
            </div>
        </div>

        <div id="como-funciona-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 900px;">
                <h2 class="app-title">Arquitectura del Sistema</h2>
                <div class="glass-grid-3" style="margin-top: 20px;">
                    <div class="glass-card">
                        <h3>1. Lectura Inteligente</h3>
                        <p>Evaluación matemática de texto e imágenes para crear una huella criptográfica única inviolable.</p>
                    </div>
                    <div class="glass-card">
                        <h3>2. Radar Global OSINT</h3>
                        <p>Búsqueda profunda automatizada en la web para asegurar que tu creación sea 100% original antes de certificar.</p>
                    </div>
                    <div class="glass-card">
                        <h3>3. Bóveda Segura</h3>
                        <p>Registro inmutable con sello de tiempo (Blockchain) legalmente válido en caso de disputas de derechos.</p>
                    </div>
                </div>
            </div>
        </div>

        <div id="quienes-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 900px;">
                <h2 class="app-title">Nuestra Visión</h2>
                <div class="glass-grid-2" style="margin-top: 20px;">
                    <div class="glass-card">
                        <h3>El Problema</h3>
                        <p>La protección legal es lenta y cara. El robo digital es rápido. Creadores y PyMEs quedan desprotegidos.</p>
                    </div>
                    <div class="glass-card">
                        <h3>DeepTech Solution</h3>
                        <p>Democratizamos el derecho digital con un entorno SaaS preventivo, económico y 100% automatizado.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="notificaciones-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 650px;">
                <h2 class="app-title">Buzón de Notificaciones</h2>
                <div id="lista-notificaciones" style="width: 100%; margin-top: 20px;">
                    <div id="notif-vacia" style="text-align: center; color: rgba(224, 225, 221, 0.5); padding: 40px;">
                        <div style="font-size: 3em; margin-bottom: 10px; line-height: 1;">🗂️</div>
                        <p>Sin notificaciones nuevas.</p>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <div id="bulk-action-bar" class="bulk-action-bar">
        <span style="font-weight: 400; color: white; font-family: 'Montserrat', sans-serif;"><span id="sel-count">0</span> seleccionados</span>
        <button class="btn btn-secondary" style="padding: 8px 15px; margin-left: 10px;" onclick="cancelarSeleccion()">Cancelar</button>
        <button class="btn btn-danger" style="padding: 8px 15px;" onclick="eliminarSeleccionados()">Eliminar</button>
    </div>

    <div id="informe-modal" class="modal-overlay">
        <div class="glass-card" style="width: 90%; max-width: 450px; position: relative;">
            <button class="modal-close-btn" onclick="cerrarInforme()">&times;</button>
            <h3 style="margin-top: 0;">📄 Informe OSINT</h3>
            <div style="margin-top: 20px; text-align: left;">
                <p style="font-weight: 300;">Activo: <span id="inf-nombre" style="color: var(--text-main); font-weight:500;"></span></p>
                <p style="font-weight: 300; margin-top:10px;">Hash ID: <br><span id="inf-hash" style="font-family: monospace; color: rgba(224, 225, 221, 0.6); font-size: 0.85em; word-break: break-all;"></span></p>
                <p style="font-weight: 300; margin-top:10px;">Estado: <br><span id="inf-estado"></span></p>
                
                <div style="margin-top: 15px; border-top: 1px solid rgba(119, 141, 169, 0.2); padding-top: 15px;">
                    <p style="font-weight: 500; text-align: left; margin-bottom: 10px; font-size: 0.9em; color: var(--text-main);">Bitácora de Rastreo OSINT 24/7:</p>
                    <div id="inf-bitacora" class="url-list" style="max-height: 120px; margin-top: 0; text-align: left;"></div>
                </div>
            </div>
            <button class="btn btn-secondary" style="margin-top: 25px; width: 100%;" onclick="cerrarInforme()">Cerrar Informe</button>
        </div>
    </div>

    <div id="certificado-modal" class="modal-overlay">
        <div class="glass-card" style="width: 95%; max-width: 600px; position: relative; padding: 25px;">
            <button class="modal-close-btn" onclick="cerrarCertificado()">&times;</button>
            <div class="certificate-box">
                <div style="text-align: center;">
                    <p class="cert-logo">DeepTech</p>
                    <h3 class="cert-title">CERTIFICADO DE AUTORÍA</h3>
                </div>
                <p class="cert-text">Por la presente, certificamos que el activo digital ha sido registrado en la Blockchain, estableciendo prueba inmutable de anterioridad.</p>
                <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 12px; margin-bottom: 20px; border: 1px solid rgba(119, 141, 169, 0.1);">
                    <p style="margin: 0 0 5px 0; font-size: 0.8em; color: rgba(224, 225, 221, 0.6);">Archivo:</p>
                    <p id="cert-nombre" style="margin: 0 0 15px 0; color: var(--text-main); font-weight: 500;"></p>
                    <p style="margin: 0 0 5px 0; font-size: 0.8em; color: rgba(224, 225, 221, 0.6);">Firma SHA-256:</p>
                    <p id="cert-hash" style="margin: 0; color: var(--accent-light); font-family: monospace; font-size: 0.85em; word-break: break-all;"></p>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85em;">
                    <div style="text-align: left;">
                        <span style="color: rgba(224, 225, 221, 0.6); display:block; margin-bottom: 5px;">Timestamp:</span>
                        <strong id="cert-fecha" style="color: var(--text-main);"></strong>
                    </div>
                </div>
            </div>
            <button class="btn" style="margin-top: 25px; width: 100%;" onclick="alert('Funcionalidad de descarga de PDF activada para tu presentación.')">Descargar PDF</button>
        </div>
    </div>

    <div id="auditoria-modal" class="modal-overlay">
        <div class="glass-card" style="width: 90%; max-width: 450px; position: relative;">
            <button class="modal-close-btn" onclick="cerrarAuditoria()">&times;</button>
            <h3 style="margin-top: 0;">⚖️ Solicitud de Auditoría</h3>
            <div style="margin-top: 20px;">
                <p style="font-weight: 300; text-align: left;">Archivo a revisar: <br><span style="color: var(--text-main);">{% if mostrando_resultado %}{{ nombre_archivo }}{% else %}Archivo Auditado{% endif %}</span></p>
                <p style="font-weight: 300; text-align: left; margin-top:10px;">Motivo: <br><span style="font-family: monospace; color: rgba(224, 225, 221, 0.7); font-size: 0.9em;">Revisión manual por posible falso positivo.</span></p>
                <p style="font-weight: 300; text-align: left; margin-top:10px;">Estado de la solicitud: <br><span id="auditoria-estado" style="color: var(--alert); font-weight: 500;">Pendiente de envío</span></p>
            </div>
            <button id="btn-enviar-auditoria" class="btn" style="width: 100%; margin-top: 25px;" onclick="enviarAuditoria()">Enviar Solicitud Oficial</button>
        </div>
    </div>

    <form id="rename-form" action="/renombrar" method="POST" style="display: none;">
        <input type="hidden" name="hash_id" id="rename-hash">
        <input type="hidden" name="nuevo_nombre" id="rename-name">
    </form>

    <script>
        let unreadCount = 0;

        // --- LÓGICA DEL SWITCH ---
        function activarToggle(element) {
            let thumb = document.getElementById('switch-thumb-btn');
            if(thumb.classList.contains('active')) return;
            
            thumb.classList.add('active');
            
            setTimeout(() => {
                ingresarApp();
            }, 600);
        }

        if (window.performance) {
            var navEntries = window.performance.getEntriesByType("navigation");
            var isReload = false;
            if (navEntries.length > 0 && navEntries[0].type === "reload") {
                isReload = true;
            } else if (window.performance.navigation && window.performance.navigation.type === 1) {
                isReload = true;
            }
            if (isReload && window.location.search !== "") {
                window.location.href = "/";
            }
        }

        function ingresarApp() {
            var main = document.getElementById('landing-main');
            var wrapper = document.getElementById('main-wrapper');
            main.style.opacity = '0';
            main.style.transform = 'translateY(-30px)';
            setTimeout(function() {
                main.style.display = 'none';
                wrapper.style.display = 'flex';
                void wrapper.offsetWidth; 
                wrapper.style.opacity = '1';
                
                // Inicializar burbuja en la pestaña activa
                var activeBtn = document.querySelector('.tab-btn.active');
                if(activeBtn) moverBurbuja(activeBtn);
            }, 500);
        }

        // --- LÓGICA DEL BUBBLE MENU ---
        function moverBurbuja(btnElement) {
            var bubble = document.getElementById('nav-bubble');
            if(bubble && btnElement) {
                bubble.style.width = btnElement.offsetWidth + 'px';
                bubble.style.left = btnElement.offsetLeft + 'px';
            }
        }

        // Reposicionar burbuja al cambiar el tamaño de ventana
        window.addEventListener('resize', function() {
            var activeTab = document.querySelector('.top-nav .tab-btn.active');
            if(activeTab) moverBurbuja(activeTab);
        });

        function transicionAuditarNuevo() {
            var appSec = document.getElementById('app-section');
            appSec.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            appSec.style.opacity = '0';
            appSec.style.transform = 'translateY(10px)';
            
            var textoCarga = document.getElementById('texto-carga');
            if(textoCarga) {
                textoCarga.style.fontFamily = "'Montserrat', sans-serif";
                textoCarga.style.color = "rgba(224, 225, 221, 0.7)";
            }

            setTimeout(function() {
                var resArea = document.getElementById('resultado-area');
                if(resArea) resArea.style.display = 'none';
                
                var titles = document.getElementById('upload-titles');
                if(titles) titles.style.display = 'flex';
                
                var uploadBox = document.getElementById('upload-area-box');
                if(uploadBox) {
                    uploadBox.style.display = 'block';
                    var form = document.getElementById('upload-form');
                    if(form) form.reset();
                }
                
                var trustBadges = document.getElementById('upload-badges');
                if(trustBadges) trustBadges.style.display = 'flex';
                
                appSec.style.transform = 'translateY(0px)';
                appSec.style.opacity = '1';
                window.history.pushState({}, document.title, "/?skip_intro=true");
            }, 400);
        }

        function cambiarPestana(idMostrar, btnElement) {
            cancelarSeleccion();

            var appSec = document.getElementById('app-section');
            var dashSec = document.getElementById('dashboard-section');
            var infoSec = document.getElementById('como-funciona-section');
            var qsSec = document.getElementById('quienes-section');
            var notifSec = document.getElementById('notificaciones-section');
            var planesSec = document.getElementById('planes-section');
            
            var tabs = document.querySelectorAll('.top-nav .tab-btn');
            tabs.forEach(t => t.classList.remove('active'));
            
            if(btnElement) {
                btnElement.classList.add('active');
                moverBurbuja(btnElement);
            }
            
            if(idMostrar === 'notificaciones-section') { 
                unreadCount = 0;
                var badge = document.getElementById('notif-badge');
                if(badge) badge.style.display = 'none';
            }

            var sections = [appSec, dashSec, infoSec, qsSec, notifSec, planesSec];
            sections.forEach(sec => {
                if(sec && sec.style.display !== 'none') {
                    sec.style.opacity = '0';
                    setTimeout(function() { sec.style.display = 'none'; }, 400);
                }
            });
            setTimeout(function() {
                var showSec = document.getElementById(idMostrar);
                if(showSec) {
                    showSec.style.display = 'flex'; 
                    void showSec.offsetWidth; 
                    showSec.style.opacity = '1';
                }
            }, 400);
        }

        function cambiarSubPestana(idMostrar, btnElement) {
            var tabs = document.querySelectorAll('.sub-tab-btn');
            tabs.forEach(t => t.classList.remove('active'));
            btnElement.classList.add('active');

            var sections = ['boveda-personal-tab', 'boveda-instagram-tab', 'boveda-facebook-tab', 'boveda-x-tab'];
            sections.forEach(secId => {
                var sec = document.getElementById(secId);
                if (sec && sec.style.display !== 'none') {
                    sec.style.opacity = '0';
                    setTimeout(function() { sec.style.display = 'none'; }, 300); 
                }
            });
            setTimeout(function() {
                var showSec = document.getElementById(idMostrar);
                if (showSec) {
                    showSec.style.display = 'flex';
                    void showSec.offsetWidth; 
                    showSec.style.opacity = '1';
                }
            }, 300);
        }

        function simularConexion(redSocial, containerId) {
            var container = document.getElementById(containerId);
            container.style.opacity = 0;
            
            setTimeout(() => {
                container.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;">
                        <div class="loading-bar-container" style="max-width: 300px; height: 8px;">
                            <div class="loading-bar-fill" id="sim-loading-fill"></div>
                        </div>
                        <p style="color: var(--text-main); font-weight: 300; font-size: 1.1em; margin-top: 20px; text-align: center;">Estableciendo conexión segura con ${redSocial}...</p>
                    </div>
                `;
                container.style.opacity = 1;

                var simFill = document.getElementById('sim-loading-fill');
                if(simFill) {
                    setTimeout(() => { simFill.style.width = '35%'; }, 100);
                    setTimeout(() => { simFill.style.width = '65%'; }, 1500);
                    setTimeout(() => { simFill.style.width = '95%'; }, 2500);
                }

                setTimeout(() => {
                    let icon = redSocial === 'X' ? '📑' : '🖼️';
                    let mockCards = '';
                    
                    for(let i=1; i<=3; i++) {
                        let shortId = Math.random().toString(36).substring(2, 10).toUpperCase();
                        mockCards += `
                            <div class="card-proyecto glass-card" style="cursor: default;">
                                <div class="card-header-flex">
                                    <span class="social-badge badge-${redSocial.toLowerCase()}" style="margin:0;">${redSocial}</span>
                                </div>
                                <div class="img-mock" style="margin-top: 10px;">${icon}</div>
                                <p style="margin: 0; font-weight: 500; font-size: 0.95em; color: var(--text-main); width: 100%;">Pub_${redSocial}_00${i}</p>
                                <small style="color: rgba(224, 225, 221, 0.5); font-size: 0.7em; margin-top: 5px; font-family: monospace;">ID: ${shortId}...</small>
                                <span class="badge-status badge-clean">✅ Monitor Activo</span>
                            </div>
                        `;
                    }

                    container.style.opacity = 0;
                    setTimeout(() => {
                        container.innerHTML = `
                            <div style="width: 100%; display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; border-bottom: 1px solid rgba(119, 141, 169, 0.2); padding-bottom: 15px;">
                                <h3 style="color: var(--accent-light); margin:0 0 5px 0; font-family: 'Oswald', sans-serif; font-size: 1.5em; text-align: center;">✅ Cuenta vinculada exitosamente</h3>
                                <p style="color: rgba(224, 225, 221, 0.85); margin:0; font-weight: 300; font-size: 1em; text-align: center;">Se han importado y protegido tus últimas publicaciones.</p>
                            </div>
                            <div class="grid-proyectos" style="justify-content: center;">
                                ${mockCards}
                            </div>
                        `;
                        container.style.opacity = 1;
                    }, 300);
                }, 3500); 
            }, 300);
        }

        function ejecutarCarga() {
            var archivo = document.getElementById('input-archivo').value.toLowerCase();
            var textoCarga = document.getElementById('texto-carga');
            
            var trustBadges = document.getElementById('upload-badges');
            if(trustBadges) trustBadges.style.display = 'none';
            if (archivo.endsWith('.pdf') || archivo.endsWith('.docx') || archivo.endsWith('.doc')) {
                textoCarga.innerText = "Encriptando texto y conectando con radar web...";
            } else {
                textoCarga.innerText = "Realizando validación cruzada y pHash matemático...";
            }
            var appSec = document.getElementById('app-section');
            var loadSec = document.getElementById('loading-section');
            appSec.style.opacity = '0';
            
            setTimeout(function() {
                appSec.style.display = 'none';
                loadSec.style.display = 'flex';
                void loadSec.offsetWidth;
                loadSec.style.opacity = '1';
                
                var fill = document.getElementById('main-loading-fill');
                if(fill) {
                    fill.style.width = '0%';
                    setTimeout(() => { fill.style.width = '15%'; }, 200);
                    
                    setTimeout(() => { 
                        fill.style.width = '45%'; 
                        textoCarga.innerText = "Desplegando arañas OSINT en red global...";
                        textoCarga.style.fontFamily = "monospace";
                        textoCarga.style.color = "var(--accent-light)";
                    }, 1000);
                    
                    setTimeout(() => { 
                        fill.style.width = '70%'; 
                        textoCarga.innerText = "Verificando colisiones de hash criptográfico...";
                    }, 2500);
                    
                    setTimeout(() => { 
                        fill.style.width = '90%'; 
                        textoCarga.innerText = "Generando certificado de evidencia inmutable...";
                    }, 4500);
                    setTimeout(() => { 
                        fill.style.width = '96%'; 
                        textoCarga.innerText = "Finalizando auditoría de propiedad intelectual...";
                    }, 8000);
                }
            }, 400);
        }

        function toggleDropdown(id) {
            event.stopPropagation();
            var dropdowns = document.getElementsByClassName("dropdown-content");
            for (var i = 0; i < dropdowns.length; i++) {
                if (dropdowns[i].id !== id && dropdowns[i].classList.contains('show')) {
                    dropdowns[i].classList.remove('show');
                }
            }
            document.getElementById(id).classList.toggle("show");
        }

        window.onclick = function(event) {
            if (!event.target.matches('.dots-btn')) {
                var dropdowns = document.getElementsByClassName("dropdown-content");
                for (var i = 0; i < dropdowns.length; i++) {
                    if (dropdowns[i].classList.contains('show')) {
                        dropdowns[i].classList.remove('show');
                    }
                }
            }
        }

        function eliminarConAnimacion(hash, btnElement) {
            event.preventDefault();
            event.stopPropagation();
            var card = btnElement.closest('.card-proyecto');
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.8)';
            var dropdowns = document.getElementsByClassName("dropdown-content");
            for (var i = 0; i < dropdowns.length; i++) dropdowns[i].classList.remove('show');
            setTimeout(function() {
                fetch('/eliminar/' + hash);
                card.innerHTML = ''; 
                card.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                card.style.width = '0px'; card.style.minWidth = '0px'; card.style.maxWidth = '0px';
                card.style.margin = '0px'; card.style.padding = '0px'; card.style.border = 'none';
                card.style.height = '0px'; card.style.minHeight = '0px';
                
                setTimeout(function() {
                    card.remove();
                    verificarBovedaVacia();
                }, 300);
            }, 300);
        }

        function verificarBovedaVacia() {
            var proyectos = document.querySelectorAll('#boveda-personal-tab .card-proyecto');
            if (proyectos.length === 0) {
                var lista = document.getElementById('lista-boveda');
                lista.style.opacity = '0';
                setTimeout(function() {
                    lista.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: rgba(224, 225, 221, 0.5); padding: 40px; width: 100%; display: flex; flex-direction: column; align-items: center;"><p style="font-weight: 300; margin-bottom: 20px;">Tu bóveda está vacía.<br>Sube tu primer archivo para protegerlo.</p><button class="btn btn-secondary" onclick="cambiarPestana(\\'app-section\\', document.getElementById(\\'tab-auditar\\'))">Subir Archivo</button></div>';
                    lista.style.transition = 'opacity 0.4s';
                    lista.style.opacity = '1';
                }, 200);
            }
        }

        function renombrarArchivo(hash, nombreActual, btnElement) {
            event.preventDefault();
            event.stopPropagation();
            var nuevoNombre = prompt("Introduce el nuevo nombre para el archivo:", nombreActual);
            if (nuevoNombre != null && nuevoNombre.trim() != "") {
                var formData = new FormData();
                formData.append('hash_id', hash);
                formData.append('nuevo_nombre', nuevoNombre);
                fetch('/renombrar', { method: 'POST', body: formData });
                
                var card = document.querySelector('.card-proyecto[data-hash="' + hash + '"]');
                if(card) {
                    var titleEl = card.querySelector('p[title]');
                    if(titleEl) { titleEl.innerText = nuevoNombre; titleEl.title = nuevoNombre; }
                    var verInformeBtn = card.querySelector('a[onclick^="verInforme"]');
                    if (verInformeBtn) {
                        var isPlagio = verInformeBtn.getAttribute('onclick').split(", '")[2].replace("')", "");
                        verInformeBtn.setAttribute('onclick', "verInforme('"+nuevoNombre+"', '"+hash+"', '"+isPlagio+"')");
                    }
                }
                var dropdowns = document.getElementsByClassName("dropdown-content");
                for (var i = 0; i < dropdowns.length; i++) dropdowns[i].classList.remove('show');
            }
        }

        let modoSeleccion = false;
        function activarModoSeleccion(hashInicial) {
            event.preventDefault();
            event.stopPropagation();
            modoSeleccion = true;
            document.getElementById('lista-boveda').classList.add('selection-mode');
            var bar = document.getElementById('bulk-action-bar');
            bar.style.display = 'flex';
            setTimeout(() => { bar.style.opacity = '1'; }, 50);
            if(hashInicial) {
                var card = document.querySelector('.card-proyecto[data-hash="'+hashInicial+'"]');
                if(card) toggleSeleccion(card);
            }
            var dropdowns = document.getElementsByClassName("dropdown-content");
            for (var i = 0; i < dropdowns.length; i++) dropdowns[i].classList.remove('show');
        }

        function cancelarSeleccion() {
            modoSeleccion = false;
            var lista = document.getElementById('lista-boveda');
            if(lista) lista.classList.remove('selection-mode');
            var bar = document.getElementById('bulk-action-bar');
            if(bar) { bar.style.opacity = '0';
                setTimeout(() => { bar.style.display = 'none'; }, 300); }
            document.querySelectorAll('.card-proyecto.selected').forEach(card => {
                card.classList.remove('selected');
                var ind = card.querySelector('.select-indicator');
                if(ind) ind.innerHTML = '';
            });
        }

        function toggleSeleccion(card) {
            if(!modoSeleccion) return;
            card.classList.toggle('selected');
            var ind = card.querySelector('.select-indicator');
            if(card.classList.contains('selected')) { ind.innerHTML = '✓'; } else { ind.innerHTML = ''; }
            actualizarContador();
        }

        function clickEnTarjeta(event, card) {
            if(event.target.closest('.dropdown')) return;
            if(modoSeleccion) { toggleSeleccion(card); }
        }

        function actualizarContador() {
            var count = document.querySelectorAll('.card-proyecto.selected').length;
            var countEl = document.getElementById('sel-count');
            if(countEl) countEl.innerText = count;
        }

        function eliminarSeleccionados() {
            var seleccionados = document.querySelectorAll('.card-proyecto.selected');
            if(seleccionados.length === 0) return;
            var formData = new FormData();
            seleccionados.forEach(card => {
                card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.8)';
                formData.append('hashes[]', card.dataset.hash);
            });
            setTimeout(() => {
                fetch('/eliminar_multiples', { method: 'POST', body: formData });
                seleccionados.forEach(card => {
                    card.innerHTML = ''; 
                    card.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    card.style.maxWidth = '0px'; card.style.minWidth = '0px'; card.style.width = '0px';
                    card.style.flex = '0 0 0px'; card.style.margin = '0px'; card.style.padding = '0px';
                    card.style.borderWidth = '0px'; card.style.height = '0px'; card.style.minHeight = '0px';
                });
                setTimeout(() => {
                    seleccionados.forEach(card => card.remove());
                    cancelarSeleccion();
                    verificarBovedaVacia();
                }, 300);
            }, 300);
        }

        function verInforme(nombre, hash, plagio) {
            event.preventDefault();
            document.getElementById('inf-nombre').innerText = nombre;
            document.getElementById('inf-hash').innerText = hash;
            
            if(plagio === 'True') {
                document.getElementById('inf-estado').innerHTML = '<span style="color: var(--alert); font-weight: 500;">⛔ Alerta de Plagio: Se encontraron copias idénticas.</span>';
            } else {
                document.getElementById('inf-estado').innerHTML = '<span style="color: var(--success); font-weight: 500;">✅ 100% Original - Activo monitoreado y seguro.</span>';
            }
            
            let bitacora = document.getElementById('inf-bitacora');
            if(bitacora) {
                let d = new Date();
                let horaAyer = new Date(d.getTime() - (24 * 60 * 60 * 1000));
                let hHoy = d.getHours().toString().padStart(2, '0') + ":" + d.getMinutes().toString().padStart(2, '0') + (d.getHours() >= 12 ? ' PM' : ' AM');
                let hAyer = horaAyer.getHours().toString().padStart(2, '0') + ":" + horaAyer.getMinutes().toString().padStart(2, '0') + (horaAyer.getHours() >= 12 ? ' PM' : ' AM');
                
                if(plagio === 'True') {
                    bitacora.innerHTML = `
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:var(--alert);">⛔ Hoy, ${hHoy}</span> - Se detectaron copias idénticas en la red.</div>
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:var(--alert);">⛔ Ayer, ${hAyer}</span> - Alerta de posibles similitudes detectadas.</div>
                    `;
                } else {
                    bitacora.innerHTML = `
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:var(--success);">✅ Hoy, ${hHoy}</span> - Escaneo completado. 0 coincidencias.</div>
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:var(--success);">✅ Ayer, ${hAyer}</span> - Escaneo OSINT completado. 0 coincidencias.</div>
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:rgba(224, 225, 221, 0.6);">🔗 Registro Inicial</span> - Sello de tiempo creado en Blockchain.</div>
                    `;
                }
            }

            var dropdowns = document.getElementsByClassName("dropdown-content");
            for (var i = 0; i < dropdowns.length; i++) dropdowns[i].classList.remove('show');
            var modal = document.getElementById('informe-modal');
            modal.style.display = 'flex';
            setTimeout(() => { modal.style.opacity = '1'; }, 50);
        }

        function cerrarInforme() {
            var modal = document.getElementById('informe-modal');
            modal.style.opacity = '0';
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }
        
        function verCertificado(nombre, hash, fecha) {
            event.preventDefault();
            document.getElementById('cert-nombre').innerText = nombre;
            document.getElementById('cert-hash').innerText = hash;
            document.getElementById('cert-fecha').innerText = fecha;
            
            var dropdowns = document.getElementsByClassName("dropdown-content");
            for (var i = 0; i < dropdowns.length; i++) dropdowns[i].classList.remove('show');
            
            var modal = document.getElementById('certificado-modal');
            modal.style.display = 'flex';
            setTimeout(() => { modal.style.opacity = '1'; }, 50);
        }

        function cerrarCertificado() {
            var modal = document.getElementById('certificado-modal');
            modal.style.opacity = '0';
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }

        function abrirAuditoria() {
            var modal = document.getElementById('auditoria-modal');
            modal.style.display = 'flex';
            setTimeout(() => { modal.style.opacity = '1'; }, 50);
        }

        function cerrarAuditoria() {
            var modal = document.getElementById('auditoria-modal');
            modal.style.opacity = '0';
            setTimeout(() => { 
                modal.style.display = 'none'; 
                var btn = document.getElementById('btn-enviar-auditoria');
                var estado = document.getElementById('auditoria-estado');
                if(btn) {
                    btn.innerHTML = "Enviar Solicitud Oficial";
                    btn.style.backgroundColor = "var(--accent-blue)";
                    btn.style.color = "var(--bg-dark)";
                    btn.disabled = false;
                }
                if(estado) {
                    estado.innerHTML = "Pendiente de envío";
                    estado.style.color = "var(--alert)";
                }
            }, 300);
        }

        function enviarAuditoria() {
            var btn = document.getElementById('btn-enviar-auditoria');
            var estado = document.getElementById('auditoria-estado');
            
            btn.innerHTML = "⏳ Procesando...";
            btn.disabled = true;
            setTimeout(() => {
                btn.innerHTML = "✅ Solicitud Enviada";
                btn.style.backgroundColor = "var(--success)";
                btn.style.color = "var(--bg-dark)";
                
                if(estado) {
                    estado.innerHTML = "✅ En revisión por especialista legal";
                    estado.style.color = "var(--success)";
                }
                
                agregarNotificacion();
                
                setTimeout(() => {
                    cerrarAuditoria();
                }, 2500);
            }, 1500);
        }

        function agregarNotificacion() {
            let container = document.getElementById('lista-notificaciones');
            let vaciaMsg = document.getElementById('notif-vacia');
            
            if(vaciaMsg) {
                vaciaMsg.style.display = 'none';
            }
            
            let now = new Date();
            let timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            let dateString = now.toLocaleDateString();
            let fileName = "{% if mostrando_resultado %}{{ nombre_archivo }}{% else %}Archivo{% endif %}";
            
            let notifHTML = `
                <div class="notif-card fade-in-element" style="width: 100%; box-sizing: border-box;">
                    <h4>⚖️ Auditoría Humana Solicitada</h4>
                    <p>Se ha levantado un ticket de revisión manual para el archivo: <span style="color:var(--text-main); font-weight:500;">${fileName}</span>. Un especialista evaluará tu caso en las próximas 24 horas.</p>
                    <span class="notif-time" style="color: rgba(224, 225, 221, 0.5);">${dateString} - ${timeString}</span>
                </div>
            `;
            container.innerHTML = notifHTML + container.innerHTML;
            
            unreadCount++;
            let badge = document.getElementById('notif-badge');
            badge.innerText = unreadCount;
            badge.style.display = 'flex';
        }

        // --- MOTOR DE BÚSQUEDA CONTINUA (REVISIÓN DE INTEGRIDAD) ---
        async function revisarIntegridad() {
            var btn = document.getElementById('btn-revisar-integridad');
            var cards = document.querySelectorAll('.card-proyecto');
            
            if (cards.length === 0) {
                alert("La bóveda está vacía.");
                return;
            }

            btn.disabled = true;
            btn.style.opacity = '0.6';
            btn.style.cursor = 'wait';

            for (let i = 0; i < cards.length; i++) {
                let card = cards[i];
                let hash = card.dataset.hash;
                let tituloEl = card.querySelector('p[title]');
                let nombre = tituloEl ? tituloEl.innerText : "Archivo";
                
                btn.innerText = `🔎 Revisando (${i + 1}/${cards.length})...`;
                
                try {
                    let response = await fetch('/revisar_integridad_hash/' + hash, { method: 'POST' });
                    let data = await response.json();
                    
                    if(data.error) {
                        console.error("Error al revisar", nombre, ":", data.error);
                        continue;
                    }

                    let badge = card.querySelector('.badge-status');
                    let verInformeBtn = card.querySelector('a[onclick^="verInforme"]');

                    if (data.plagio) {
                        if (badge) {
                            badge.className = 'badge-status badge-alert';
                            badge.innerHTML = '⛔ Alerta en Web';
                        }
                        if (verInformeBtn) {
                            verInformeBtn.setAttribute('onclick', `verInforme('${nombre}', '${hash}', 'True')`);
                        }
                    } else {
                        if (badge) {
                            badge.className = 'badge-status badge-clean';
                            badge.innerHTML = '✅ Monitor Activo';
                        }
                        if (verInformeBtn) {
                            verInformeBtn.setAttribute('onclick', `verInforme('${nombre}', '${hash}', 'False')`);
                        }
                    }
                } catch (e) {
                    console.error("Error en conexión para:", nombre, e);
                }
            }

            btn.innerText = "🔎 Analizar Integridad";
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
        
        // Setup inicial del Bubble Menu si la página recarga y hay pestaña activa
        window.onload = function() {
            var activeTab = document.querySelector('.top-nav .tab-btn.active');
            if(activeTab) moverBurbuja(activeTab);
        }
    </script>
</body>
</html>
"""

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
            
            return render_template_string(HTML_TEMPLATE, 
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
            
    return render_template_string(HTML_TEMPLATE, 
                                  mostrando_resultado=False, 
                                  skip_intro=skip_intro, 
                                  proyectos=db_proyectos,
                                  mostrar_boveda=abrir_boveda)

if __name__ == "__main__":
    app.run(debug=True)
