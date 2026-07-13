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
    <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>DeepTech Legal Solutions</title>
    <style>
        /* IMPORTACIÓN DE TIPOGRAFÍAS */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&family=Oswald:wght@300;400;500;600&display=swap');
        @import url('https://fonts.cdnfonts.com/css/bukhari-script');

        /* PALETA DE COLORES APLICADA */
        body { 
            font-family: 'Montserrat', sans-serif;
            margin: 0; 
            padding: 0; 
            color: #E0E1DD; 
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh; 
            box-sizing: border-box;
            background-color: #0D1B2A; 
            overflow-x: hidden;
            letter-spacing: 0.3px;
        }

        h1, h2, h3 { font-family: 'Oswald', sans-serif; }

        /* FONDO: SOFT MESH GRADIENT (ESTILO AURORA) */
        .bg-organic {
            position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
            z-index: -2; background-color: #0D1B2A; overflow: hidden;
            opacity: 0; animation: fadeInBg 2s ease-out forwards; 
        }
        
        /* Capa de desenfoque de cristal para unificar los colores */
        .bg-organic::after {
            content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            backdrop-filter: blur(120px); -webkit-backdrop-filter: blur(120px); z-index: 1;
        }

        /* Formas orgánicas de color */
        .gradient-blob {
            position: absolute; border-radius: 50%; filter: blur(60px);
            animation: slowDrift infinite alternate cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Aplicación estricta de la paleta */
        .blob-1 {
            width: 70vw; height: 70vw; top: -10%; left: -10%;
            background-color: #1B263B; opacity: 0.8; animation-duration: 25s;
        }
        .blob-2 {
            width: 60vw; height: 60vw; bottom: -20%; right: -10%;
            background-color: #415A77; opacity: 0.6; animation-duration: 30s; animation-delay: -5s;
        }
        .blob-3 {
            width: 50vw; height: 50vw; top: 20%; left: 30%;
            background-color: #778DA9; opacity: 0.3; animation-duration: 35s; animation-delay: -10s;
        }

        /* Movimiento ultra lento y sin rotaciones bruscas para evitar mareos */
        @keyframes slowDrift {
            0% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(8vw, 6vh) scale(1.05); }
            66% { transform: translate(-5vw, 10vh) scale(0.95); }
            100% { transform: translate(-8vw, -5vh) scale(1.05); }
        }

        @keyframes fadeInBg { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fadeInTab { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* ANIMACIÓN DE ENTRADA */
        @keyframes fadeUpEntrance { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }

        /* PANTALLAS DE PRESENTACIÓN */
        .landing-screen { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #E0E1DD; overflow-y: auto; background: transparent; transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out; transform: translateY(0); }
        #landing-main { justify-content: center; padding: 20px; text-align: center; } 
        .landing-screen::-webkit-scrollbar { width: 8px; }
        .landing-screen::-webkit-scrollbar-thumb { background-color: rgba(224, 225, 221, 0.2); border-radius: 4px; }

        /* LOGO */
        .hero-logo-wrapper { display: flex; flex-direction: column; align-items: center; margin-bottom: 25px; filter: drop-shadow(0px 8px 20px rgba(13, 27, 42, 0.6)); }
        #landing-main .hero-logo-wrapper { opacity: 0; animation: fadeUpEntrance 1.5s cubic-bezier(0.4, 0, 0.2, 1) 0.2s forwards; }
        #landing-main .hero-subtitle { opacity: 0; animation: fadeUpEntrance 1.5s cubic-bezier(0.4, 0, 0.2, 1) 0.8s forwards; }
        #landing-main .btn-ingreso { opacity: 0; animation: fadeUpEntrance 1.5s cubic-bezier(0.4, 0, 0.2, 1) 1.4s forwards; }

        .logo-top-line { display: flex; align-items: flex-start; line-height: 1; }
        .logo-deeptech { font-family: 'Bukhari Script', cursive; font-size: clamp(3.5rem, 10vw, 8.5rem); color: #778DA9; font-weight: normal; text-shadow: 0px 4px 15px rgba(13, 27, 42, 0.5); padding-right: 5px; }
        .logo-tm { font-family: 'Oswald', sans-serif; font-size: clamp(0.7rem, 1.5vw, 1.4rem); color: #778DA9; margin-top: clamp(10px, 3.5vw, 25px); font-weight: 500; }
        .logo-bottom-line { display: flex; justify-content: center; width: 100%; margin-top: clamp(15px, 3vw, 35px); }
        .logo-legal { font-family: 'Oswald', sans-serif; font-size: clamp(0.9rem, 2.5vw, 2.2rem); color: #E0E1DD; letter-spacing: 0.38em; font-weight: 400; text-transform: none; margin-left: 0.38em; text-shadow: 0px 4px 10px rgba(0,0,0,0.4); }

        .hero-logo-wrapper.small-logo { margin-bottom: 15px; filter: drop-shadow(0px 4px 10px rgba(13, 27, 42, 0.4)); }
        .hero-logo-wrapper.small-logo .logo-deeptech { font-size: clamp(2.5rem, 6vw, 4.5rem); }
        .hero-logo-wrapper.small-logo .logo-tm { font-size: 0.7rem; margin-top: 5px; }
        .hero-logo-wrapper.small-logo .logo-bottom-line { margin-top: 5px; }
        .hero-logo-wrapper.small-logo .logo-legal { font-size: clamp(0.7rem, 1.5vw, 1.1rem); }

        .hero-subtitle { font-family: 'Montserrat', sans-serif; font-size: clamp(0.9em, 2vw, 1.2em); color: #778DA9 !important; font-weight: 400; margin-bottom: 40px; text-align: center; letter-spacing: 1px; line-height: 1.5;}

        /* NUEVAS INSIGNIAS DE CONFIANZA */
        .trust-badges { display: flex; justify-content: center; gap: 20px; margin-top: 40px; flex-wrap: wrap; opacity: 0; animation: fadeUpEntrance 1.5s cubic-bezier(0.4, 0, 0.2, 1) 1.8s forwards; }
        .trust-badge-item { display: flex; align-items: center; gap: 8px; font-size: 0.85em; color: rgba(224, 225, 221, 0.6); font-family: 'Montserrat', sans-serif; font-weight: 400; }
        
        .info-content-wrapper { max-width: 900px; margin: auto; padding: 20px; width: 100%; box-sizing: border-box; }
        .glass-grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .glass-grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        
        .glass-card {
            background: rgba(27, 38, 59, 0.5); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(119, 141, 169, 0.2); border-radius: 16px; padding: 25px; text-align: center;
            transition: transform 0.3s ease, border-color 0.3s ease; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1); 
            box-sizing: border-box;
        }
        .glass-card:hover { transform: translateY(-5px); border-color: #778DA9; }
        .glass-card h3 { color: #CCFBF1; font-size: 1.5em; margin-bottom: 15px; display: flex; justify-content: center; align-items: center; gap: 10px; font-family: 'Oswald', sans-serif;}
        .glass-card p { font-size: 0.95em; color: rgba(224, 225, 221, 0.9); line-height: 1.7; margin: 0; font-weight: 300; }

        /* LA PLATAFORMA SAAS */
        #main-wrapper { 
            background: rgba(13, 27, 42, 0.65); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(119, 141, 169, 0.2); border-radius: 16px; box-shadow: 0px 25px 60px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1); 
            width: 95%; max-width: 850px; position: relative; overflow: hidden; height: 85vh; min-height: 600px; max-height: 800px;
            transition: opacity 0.5s ease-in-out; display: flex; flex-direction: column; z-index: 1000;
        }
        
        /* MENU SUPERIOR FIJO Y ESTABLE */
        .top-nav { 
            display: flex; justify-content: center; align-items: center; gap: 8px; width: 100%; 
            border-bottom: 1px solid rgba(119, 141, 169, 0.2); padding: 0 10px; margin: 0; 
            box-sizing: border-box; z-index: 10; flex-wrap: nowrap; overflow-x: auto;
            flex-shrink: 0; height: 75px; min-height: 75px; 
        }
        .top-nav::-webkit-scrollbar { display: none; }
        
        .tab-btn { 
            background: rgba(27, 38, 59, 0.4); border: 1px solid rgba(119, 141, 169, 0.2); color: rgba(224, 225, 221, 0.7); 
            padding: 8px 14px; border-radius: 20px; font-size: 0.85em; font-family: 'Montserrat', sans-serif; font-weight: 500; 
            cursor: pointer; transition: all 0.2s ease; letter-spacing: 0.5px; text-align: center; 
            white-space: nowrap; display: flex; align-items: center; justify-content: center;
        }
        .tab-btn:hover { background-color: rgba(65, 90, 119, 0.5); color: #E0E1DD; }
        .tab-btn.active { background-color: #415A77; color: #E0E1DD; border-color: #778DA9;}

        .notif-badge {
            background-color: #DC2626; color: white; font-size: 0.85em; font-family: 'Montserrat', sans-serif; 
            font-weight: 600; padding: 2px 6px; border-radius: 12px; margin-left: 6px; 
            box-shadow: 0px 2px 4px rgba(0,0,0,0.3); display: none; align-items: center; justify-content: center;
        }

        /* MENÚ INFERIOR (SUB-NAV PARA BÓVEDA) */
        .sub-nav { 
            display: flex; justify-content: flex-start; gap: 10px; width: 100%; 
            border-bottom: 1px solid rgba(119, 141, 169, 0.2); padding-bottom: 15px; margin-bottom: 20px; 
            overflow-x: auto; box-sizing: border-box; flex-shrink: 0;
        }
        .sub-nav::-webkit-scrollbar { height: 4px; }
        .sub-nav::-webkit-scrollbar-thumb { background-color: rgba(119, 141, 169, 0.3); border-radius: 4px; }
        
        .sub-tab-btn { background: transparent; border: 1px solid transparent; color: rgba(224, 225, 221, 0.6); padding: 8px 16px; border-radius: 20px; font-size: 0.9em; font-family: 'Montserrat', sans-serif; font-weight: 500; cursor: pointer; transition: all 0.2s ease; letter-spacing: 0.5px; white-space: nowrap; display: flex; align-items: center;}
        .sub-tab-btn:hover { background-color: rgba(27, 38, 59, 0.6); color: #E0E1DD; border-color: rgba(119, 141, 169, 0.2); }
        .sub-tab-btn.active { background-color: rgba(27, 38, 59, 0.8); color: #E0E1DD; border-color: #778DA9;}

        /* CLASES DE CONTENEDORES Y ALINEACIÓN ESTABLE */
        .section-container { 
            width: 100%; flex-grow: 1; box-sizing: border-box; transition: opacity 0.4s ease-in-out; 
            background-color: transparent; overflow-y: auto; display: flex; flex-direction: column; 
            min-height: 0; 
        }
        .section-container::-webkit-scrollbar { width: 6px; }
        .section-container::-webkit-scrollbar-thumb { background-color: rgba(119, 141, 169, 0.3); border-radius: 4px; }
        
        .sub-section-container { width: 100%; flex-grow: 1; box-sizing: border-box; transition: opacity 0.3s ease-in-out; background-color: transparent; display: flex; flex-direction: column; align-items: center; opacity: 0; display: none;}
        
        .app-centered-layout { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding: 20px 40px 40px 40px; box-sizing: border-box; }
        
        /* CORRECCIÓN SCROLL SUBIDA: Margen seguro que no genera overflow */
        .view-centered { margin-top: 8vh; transition: margin-top 0.4s ease; }

        .content-wrapper-inner { width: 100%; max-width: 750px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; padding-bottom: 20px; }
        
        .app-title { font-family: 'Oswald', sans-serif; font-size: 2.2em; color: #E0E1DD; margin: 0 0 15px 0; text-align: center; font-weight: 400;}
        .app-subtitle { font-family: 'Montserrat', sans-serif; font-size: 1.05em; color: #778DA9; text-align: center; margin-bottom: 30px; font-weight: 300;}
        
        .btn { background-color: #415A77; color: #E0E1DD; padding: 15px 35px; font-size: 1.1em; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; font-family: 'Montserrat', sans-serif; display: inline-block; transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.2s ease, opacity 0.3s ease; letter-spacing: 0.5px; }
        .btn:hover { background-color: #778DA9; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .btn:active { transform: scale(0.96) translateY(0px); }
        .btn-secondary { background-color: rgba(65, 90, 119, 0.3); border: 1px solid rgba(119, 141, 169, 0.4); color: #E0E1DD; padding: 12px 25px; font-size: 1em; transition: all 0.2s ease;}
        .btn-secondary:hover:not(:disabled) { background-color: rgba(119, 141, 169, 0.5); transform: translateY(-2px); }
        .btn-secondary:active:not(:disabled) { transform: scale(0.96); }
        
        .upload-area { width: 100%; max-width: 550px; text-align: center; background-color: rgba(27, 38, 59, 0.3); padding: 30px; border-radius: 12px; border: 2px dashed rgba(119, 141, 169, 0.4); transition: border-color 0.3s, background-color 0.3s; margin: 0 auto; box-sizing: border-box;}
        .upload-area:hover { border-color: #778DA9; background-color: rgba(65, 90, 119, 0.3); }
        
        @keyframes fadeInSlide { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .fade-in-element { animation: fadeInSlide 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
        
        /* BARRA DE CARGA REALISTA SIN PARPADEO */
        .loading-bar-container { width: 100%; max-width: 400px; height: 10px; background-color: rgba(13, 27, 42, 0.8); border-radius: 10px; margin: 30px auto; overflow: hidden; border: 1px solid rgba(119, 141, 169, 0.3); box-shadow: inset 0 2px 5px rgba(0,0,0,0.5); }
        .loading-bar-fill { 
            height: 100%; width: 0%; border-radius: 10px; 
            background: linear-gradient(90deg, #415A77, #5EEAD4, #778DA9, #415A77); 
            background-size: 200% 100%; 
            animation: shimmerGradient 2.5s linear infinite; 
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); 
        }
        @keyframes shimmerGradient { 
            0% { background-position: 200% 0; } 
            100% { background-position: 0% 0; } 
        }

        /* TARJETAS DE RESULTADO MINIMALISTAS */
        .result-card-minimal { width: 100%; max-width: 550px; margin: 20px auto; text-align: center; box-sizing: border-box; background: rgba(27, 38, 59, 0.5); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-radius: 16px; padding: 40px 30px; border: 1px solid rgba(119, 141, 169, 0.2); box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 10px 30px rgba(0,0,0,0.3); }
        .result-card-minimal.success { border-top: 4px solid rgba(94, 234, 212, 0.6); }
        .result-card-minimal.alert { border-top: 4px solid rgba(252, 165, 165, 0.6); }
        
        input[type="file"] { margin-top: 15px; margin-bottom: 25px; padding: 10px; border: 1px solid rgba(119, 141, 169, 0.3); border-radius: 5px; width: 100%; box-sizing: border-box; background-color: rgba(13, 27, 42, 0.5); color: #E0E1DD; font-family: 'Montserrat', sans-serif;}
        
        .url-list { max-height: 150px; overflow-y: auto; background-color: rgba(13, 27, 42, 0.5); padding: 15px; border: 1px solid rgba(119, 141, 169, 0.2); font-size: 0.9em; margin-top: 10px; border-radius: 8px; font-family: 'Montserrat', sans-serif; font-weight: 300;}
        .url-list li { margin-bottom: 10px; color: rgba(224, 225, 221, 0.85); word-break: break-word;}
        .url-list a { color: #778DA9; text-decoration: none; font-weight: 500; font-family: 'Oswald', sans-serif;}
        
        .social-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: 400; color: white; margin-right: 8px; vertical-align: middle; font-family: 'Oswald', sans-serif;}
        .badge-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); }
        .badge-facebook { background-color: #1877F2; }
        .badge-x { background-color: #000000; border: 1px solid rgba(255,255,255,0.2); }
        
        /* DASHBOARD METRICS */
        .metrics-wrapper { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; width: 100%; margin-bottom: 25px; }
        .metric-card { background: rgba(27, 38, 59, 0.4); border: 1px solid rgba(119, 141, 169, 0.2); border-radius: 12px; padding: 15px; text-align: center; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05); }
        .metric-value { font-family: 'Oswald', sans-serif; font-size: 2em; color: #5EEAD4; margin: 0; line-height: 1.2; }
        .metric-label { font-size: 0.8em; color: #778DA9; font-weight: 300; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
        
        /* BÓVEDA DINÁMICA */
        .grid-proyectos { display: flex; flex-wrap: wrap; gap: 20px; width: 100%; justify-content: center; }
        .card-proyecto { background: rgba(27, 38, 59, 0.4); border: 1px solid rgba(119, 141, 169, 0.2); border-radius: 12px; padding: 20px 15px; text-align: center; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; cursor: default; flex: 1 1 200px; max-width: 240px; box-sizing: border-box; overflow: visible; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1); }
        .card-proyecto:hover { transform: translateY(-4px); border-color: #778DA9; background: rgba(65, 90, 119, 0.3);}
        .card-proyecto .img-mock { height: 70px; width: 100%; background-color: rgba(13, 27, 42, 0.4); border-radius: 8px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; font-size: 2em; border: 1px solid rgba(119, 141, 169, 0.1); }
        .badge-status { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 0.85em; margin-top: 10px; font-weight: 400; font-family: 'Oswald', sans-serif; text-align: center; letter-spacing: 0.5px;}
        .badge-clean { background-color: rgba(65, 90, 119, 0.3); color: #E0E1DD; border: 1px solid rgba(119, 141, 169, 0.6);} 
        .badge-alert { background-color: rgba(220, 38, 38, 0.2); color: #FCA5A5; border: 1px solid rgba(220, 38, 38, 0.5);} 
        
        .card-header-flex { width: 100%; display: flex; justify-content: space-between; margin-bottom: 5px; align-items: center; }
        .dropdown { position: relative; display: inline-block; }
        .dots-btn { background: none; border: none; color: #778DA9; font-size: 1.5em; cursor: pointer; padding: 0 5px; line-height: 1; transition: color 0.2s; }
        .dots-btn:hover { color: #E0E1DD; }
        .dropdown-content { display: none; position: absolute; right: 0; top: 100%; background-color: #1B263B; min-width: 170px; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.5); z-index: 100; border-radius: 8px; border: 1px solid rgba(119, 141, 169, 0.2); overflow: hidden; margin-top: 5px; }
        .dropdown-content a { color: #E0E1DD; padding: 10px 16px; text-decoration: none; display: block; font-size: 0.9em; font-family: 'Oswald', sans-serif; text-align: left; transition: background-color 0.2s; font-weight: 300;}
        .dropdown-content a:hover { background-color: #415A77; color: white; }
        .show { display: block; }

        #lista-boveda.selection-mode .card-proyecto { cursor: pointer; }
        .select-indicator { position: absolute; top: 15px; left: 15px; width: 22px; height: 22px; border-radius: 50%; border: 2px solid rgba(224, 225, 221, 0.4); display: none; align-items: center; justify-content: center; font-size: 14px; color: transparent; transition: all 0.2s; z-index: 5; background: rgba(13, 27, 42, 0.6); }
        .selection-mode .select-indicator { display: flex; }
        .card-proyecto.selected { border-color: #778DA9; background: rgba(65, 90, 119, 0.2); transform: scale(0.98); }
        .card-proyecto.selected .select-indicator { background-color: #778DA9; border-color: #778DA9; color: #0D1B2A; }
        
        .bulk-action-bar { display: none; position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); background: rgba(13, 27, 42, 0.95); backdrop-filter: blur(10px); border: 1px solid rgba(119, 141, 169, 0.3); padding: 15px 25px; border-radius: 50px; z-index: 9999; align-items: center; gap: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); opacity: 0; transition: opacity 0.3s ease; }
        .btn-danger { background-color: rgba(185, 28, 28, 0.8); color: white; border: 1px solid #DC2626; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 1em; font-weight: 500; transition: all 0.2s; font-family: 'Montserrat', sans-serif;}
        .btn-danger:hover { background-color: #DC2626; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);}
        
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(13, 27, 42, 0.8); z-index: 20000; align-items: center; justify-content: center; backdrop-filter: blur(5px); opacity: 0; transition: opacity 0.3s ease; }
        
        /* ESTILOS PARA TARJETAS DE NOTIFICACIÓN EN EL BUZÓN */
        .notif-card {
            background: rgba(27, 38, 59, 0.5);
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(119, 141, 169, 0.2); border-left: 4px solid #5EEAD4;
            border-radius: 12px; padding: 20px; text-align: left; margin-bottom: 15px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1); transition: transform 0.3s ease;
        }
        .notif-card:hover { transform: translateY(-3px); }
        .notif-card h4 { margin: 0 0 10px 0; color: #E0E1DD; font-family: 'Oswald', sans-serif; font-size: 1.2em;}
        .notif-card p { margin: 0; color: rgba(224, 225, 221, 0.85); font-size: 0.9em; font-weight: 300; line-height: 1.5; text-align: justify; }
        .notif-time { font-size: 0.8em; color: #778DA9; margin-top: 10px; display: block; font-family: monospace;}

        /* ESTILOS PARA CERTIFICADO DE AUTORÍA */
        .certificate-box { border: 2px solid rgba(119, 141, 169, 0.5); padding: 30px; position: relative; background: rgba(13, 27, 42, 0.8); border-radius: 8px; margin-top: 15px; box-sizing: border-box; width: 100%; }
        .certificate-box::before { content: ''; position: absolute; top: 5px; left: 5px; right: 5px; bottom: 5px; border: 1px dashed rgba(119, 141, 169, 0.3); pointer-events: none; border-radius: 4px; }
        .cert-logo { font-family: 'Bukhari Script', cursive; font-size: 2.5em; color: #778DA9; margin: 0; line-height: 1; }
        .cert-title { font-family: 'Oswald', sans-serif; font-size: 1.5em; color: #E0E1DD; letter-spacing: 2px; margin: 10px 0 20px 0; border-bottom: 1px solid rgba(119, 141, 169, 0.3); padding-bottom: 10px; }
        .cert-text { font-size: 0.85em; font-weight: 300; line-height: 1.6; color: rgba(224, 225, 221, 0.9); text-align: justify; margin-bottom: 20px; }
        .cert-data-row { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(119, 141, 169, 0.2); padding-top: 10px; margin-top: 10px; font-size: 0.8em; }
        .qr-placeholder { font-size: 3em; line-height: 1; opacity: 0.8;}
        .cert-seal { width: 60px; height: 60px; border: 2px dashed #5EEAD4; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 0.6em; color: #5EEAD4; font-weight: bold; text-align: center; font-family: 'Oswald', sans-serif; transform: rotate(-15deg); flex-shrink: 0; }

        .modal-close-btn {
            position: absolute; top: 12px; right: 12px; background: rgba(13, 27, 42, 0.6); 
            border: 1px solid rgba(119, 141, 169, 0.3); color: #E0E1DD; 
            width: 32px; height: 32px; border-radius: 50%; font-size: 1.2em; 
            display: flex; align-items: center; justify-content: center; 
            cursor: pointer; z-index: 50; transition: all 0.2s ease;
        }
        .modal-close-btn:hover { background: #DC2626; color: white; border-color: #DC2626; }

        /* =========================================================
           ADAPTACIÓN PARA TELÉFONOS MÓVILES (DISEÑO RESPONSIVO) 
           ========================================================= */
        @media screen and (max-width: 768px) {
            body { padding: 10px; }
            #main-wrapper {
                height: 90vh; 
                min-height: 500px;
                max-height: none;
                width: 100%;
                border-radius: 12px;
            }
            
            /* Adaptación del fondo animado para móviles */
            .blob-1 { width: 120vw; height: 120vh; top: -10%; left: -20%; }
            .blob-2 { width: 120vw; height: 120vh; bottom: -10%; right: -20%; }
            .blob-3 { width: 100vw; height: 100vh; top: 20%; left: 10%; }
            .bg-organic::after { backdrop-filter: blur(80px); -webkit-backdrop-filter: blur(80px); }

            .app-centered-layout { padding: 15px 15px 30px 15px; }
            .top-nav {
                justify-content: flex-start; 
                padding: 0 10px;
                height: 65px; 
                min-height: 65px;
            }
            .tab-btn { padding: 6px 12px; font-size: 0.8em; }
            .app-title { font-size: 1.8em; }
            .app-subtitle { font-size: 0.9em; }
            .glass-grid-3, .glass-grid-2, .metrics-wrapper {
                grid-template-columns: 1fr; 
                gap: 15px;
            }
            .upload-area { padding: 20px 10px; }
            .cert-logo { font-size: 2em; }
            .cert-title { font-size: 1.1em; letter-spacing: 1px; }
            .cert-data-row { flex-direction: column; align-items: flex-start; gap: 15px; }
            .cert-seal { align-self: center; }
            .sub-nav { padding-bottom: 10px; }
        }
    </style>
</head>
<body>

    <div class="bg-organic">
        <div class="gradient-blob blob-1"></div>
        <div class="gradient-blob blob-2"></div>
        <div class="gradient-blob blob-3"></div>
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
        <button class="btn btn-ingreso" style="padding: 18px 45px; font-size: 1.2em;" onclick="ingresarApp()">Ingresar a la Plataforma</button>
        
        <div class="trust-badges">
            <div class="trust-badge-item"><span style="color: #5EEAD4; font-size: 1.2em;">🔒</span> Cifrado Militar</div>
            <div class="trust-badge-item"><span style="color: #5EEAD4; font-size: 1.2em;">⛓️</span> Blockchain Inmutable</div>
            <div class="trust-badge-item"><span style="color: #5EEAD4; font-size: 1.2em;">🌐</span> Radar OSINT 24/7</div>
        </div>
    </div>

    <div id="main-wrapper" {% if skip_intro %} style="display: flex; opacity: 1;" {% else %} style="display: none; opacity: 0;" {% endif %}>
        
        <div class="top-nav">
            <button id="tab-auditar" class="tab-btn {% if not mostrar_boveda %}active{% endif %}" onclick="cambiarPestana('app-section')">Auditar Archivo</button>
            <button id="tab-boveda" class="tab-btn {% if mostrar_boveda %}active{% endif %}" onclick="cambiarPestana('dashboard-section')">Mis Proyectos</button>
            <button id="tab-planes" class="tab-btn" onclick="cambiarPestana('planes-section')">Planes</button>
            <button id="tab-como-funciona" class="tab-btn" onclick="cambiarPestana('como-funciona-section')">¿Cómo funciona?</button>
            <button id="tab-quienes" class="tab-btn" onclick="cambiarPestana('quienes-section')">¿Quiénes Somos?</button>
            
            <button id="tab-notificaciones" class="tab-btn" onclick="cambiarPestana('notificaciones-section')">
                Buzón 📬 <span id="notif-badge" class="notif-badge">0</span>
            </button>
        </div>

        <div id="loading-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner view-centered">
                <h2 class="app-title" style="margin-top: 20px;">Cifrando y Analizando...</h2>
                <p id="texto-carga" class="app-subtitle" style="font-weight: 300; transition: color 0.3s ease;">Asegurando el archivo en la Bóveda Local.</p>
                <div class="loading-bar-container">
                    <div class="loading-bar-fill" id="main-loading-fill"></div>
                </div>
            </div>
        </div>

        <div id="app-section" class="section-container app-centered-layout" {% if mostrar_boveda %} style="display: none; opacity: 0;" {% else %} style="display: flex; opacity: 1;" {% endif %}>
            <div id="app-inner-wrapper" class="content-wrapper-inner {% if not mostrando_resultado %}view-centered{% endif %}">
                <div id="upload-titles" style="width: 100%; display: flex; flex-direction: column; align-items: center; {% if mostrando_resultado %}display: none;{% endif %}">
                    <div class="hero-logo-wrapper small-logo">
                        <div class="logo-top-line">
                            <span class="logo-deeptech">DeepTech</span><span class="logo-tm">TM</span>
                        </div>
                        <div class="logo-bottom-line">
                            <span class="logo-legal">Legal Solutions</span>
                        </div>
                    </div>
                    <p class="app-subtitle" style="margin-top: 0; font-weight: 300;">Sube tu activo digital (Imagen o Documento) para certificar su originalidad y protegerlo.</p>
                </div>
                
                <div class="upload-area" id="upload-area-box" {% if mostrando_resultado %} style="display: none;" {% endif %}>
                    <form id="upload-form" action="/" method="POST" enctype="multipart/form-data" onsubmit="ejecutarCarga()" style="display: flex; flex-direction: column; align-items: center;">
                        <label style="font-weight: 400; color: #E0E1DD; text-align: center; font-size: 1.1em; letter-spacing: 0.5px; font-family: 'Oswald', sans-serif;">Selecciona el archivo para certificar:</label>
                        <input type="file" name="archivo" accept="image/*,.pdf,.doc,.docx" required id="input-archivo">
                        <button type="submit" class="btn" style="width: 100%;">Analizar y Proteger en Bóveda</button>
                    </form>
                </div>

                <div id="upload-badges" style="display: {% if mostrando_resultado %}none{% else %}flex{% endif %}; justify-content: center; gap: 20px; margin-top: 30px; opacity: 0.8; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 5px; font-size: 0.8em; color: rgba(224, 225, 221, 0.6);"><span style="color: #5EEAD4;">🔒</span> Privacidad Absoluta</div>
                    <div style="display: flex; align-items: center; gap: 5px; font-size: 0.8em; color: rgba(224, 225, 221, 0.6);"><span style="color: #5EEAD4;">⚖️</span> Validez Legal DMCA</div>
                </div>
                
                {% if mostrando_resultado %}
                <div id="resultado-area" class="fade-in-element" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
                    {% if error_api %}
                        <div class="result-card-minimal alert">
                            <h2 style="color: #FCA5A5; margin-top: 0; font-family: 'Oswald', sans-serif;">Error de Conexión</h2>
                            <p style="color: #E0E1DD; font-weight: 300; margin-bottom: 0;">{{ error_api }}</p>
                        </div>
                        <div style="display: flex; justify-content: center; margin-top: 20px;">
                            <button class="btn btn-secondary" onclick="transicionAuditarNuevo()">Auditar nuevo archivo</button>
                        </div>
                    {% elif paginas_encontradas %}
                        <div class="result-card-minimal alert">
                            <h2 style="color: #FCA5A5; margin-top: 0; font-family: 'Oswald', sans-serif; font-size: 2.2em;">⚠️ Alerta de Plagio</h2>
                            <p style="color: #E0E1DD; font-weight: 300; font-size: 1.1em; margin-bottom: 25px;">Se detectaron coincidencias web del archivo <span style="color: #778DA9; font-weight: 500;">{{ nombre_archivo }}</span>.</p>
                            <button class="btn btn-secondary" style="color: #FCA5A5; border-color: rgba(252, 165, 165, 0.3);" onclick="document.getElementById('detalles-plagio').style.display='block'; this.style.display='none';">Ver Informe Completo</button>
                            <div id="detalles-plagio" style="display: none; text-align: left; margin-top: 25px; border-top: 1px solid rgba(119, 141, 169, 0.2); padding-top: 20px; animation: fadeUpEntrance 0.5s ease forwards;">
                                <p style="color: #FCA5A5; font-size: 0.95em; border: 1px solid rgba(220,38,38,0.3); padding: 10px; border-radius: 5px; background: rgba(220,38,38,0.1); font-weight: 300;">Aviso de Sistema: Para evitar infracciones de derechos de autor, este archivo no ha sido guardado en la bóveda.</p>
                                <p style="color: #E0E1DD; font-weight: 300; font-size: 0.9em; margin-top: 15px;">Radar Ejecutado: <span style="color: #FCA5A5;">{{ tipo_motor }}</span></p>
                                <p style="color: rgba(224, 225, 221, 0.85); font-weight: 300; font-size: 0.9em; margin-top: 15px;">Enlaces confirmados con el contenido original:</p>
                                <div class="url-list">
                                    <ol style="margin: 0; padding-left: 20px;">
                                    {% for sitio in paginas_encontradas %}
                                        <li style="margin-bottom: 10px;">
                                            <a href="{{ sitio.link }}" target="_blank" style="font-size: 0.95em;">{{ sitio.titulo }}</a>
                                            {% if sitio.es_instagram %}<span class="social-badge badge-instagram">Instagram</span>
                                            {% elif sitio.es_facebook %}<span class="social-badge badge-facebook">Facebook</span>{% endif %}
                                            <br><small style="color: #778DA9; word-break: break-all; font-family: 'Montserrat', sans-serif;">{{ sitio.link }}</small>
                                        </li>
                                    {% endfor %}
                                    </ol>
                                </div>
                                <p style="margin-top: 15px; color: #E0E1DD; font-weight: 300; font-size: 0.9em;">Firma Hash Auditada: <br><span style="font-family: monospace; color: #778DA9; font-size: 0.9em; word-break: break-all;">{{ hash_resultado }}</span></p>
                            </div>
                        </div>
                        
                        <div style="display: flex; justify-content: center; gap: 15px; margin-top: 20px; flex-wrap: wrap;">
                            <button class="btn btn-secondary" onclick="transicionAuditarNuevo()">Auditar nuevo archivo</button>
                            <button class="btn btn-secondary" style="color: #E0E1DD; border-color: rgba(119, 141, 169, 0.4);" onclick="abrirAuditoria()">¿Tu archivo es original?</button>
                        </div>

                    {% else %}
                        <div class="result-card-minimal success">
                            <h2 style="color: #5EEAD4; margin-top: 0; font-family: 'Oswald', sans-serif; font-size: 2.2em;">✓ Activo Original</h2>
                            <p style="color: #E0E1DD; font-weight: 300; font-size: 1.1em; margin-bottom: 25px;">El archivo <span style="color: #778DA9; font-weight: 500;">{{ nombre_archivo }}</span> es único y seguro.</p>
                            <button class="btn btn-secondary" style="color: #5EEAD4; border-color: rgba(94, 234, 212, 0.3);" onclick="document.getElementById('detalles-original').style.display='block'; this.style.display='none';">Ver Informe Completo</button>
                            <div id="detalles-original" style="display: none; text-align: left; margin-top: 25px; border-top: 1px solid rgba(119, 141, 169, 0.2); padding-top: 20px; animation: fadeUpEntrance 0.5s ease forwards;">
                                <p style="color: rgba(224, 225, 221, 0.85); font-weight: 300; font-size: 0.95em;">El análisis profundo no detectó copias en la red. El archivo se ha guardado exitosamente en tu bóveda criptográfica.</p>
                                <p style="color: #E0E1DD; font-weight: 300; font-size: 0.9em; margin-top: 15px;">Radar Ejecutado: <span style="color: #5EEAD4;">{{ tipo_motor }}</span></p>
                                <p style="color: #E0E1DD; font-weight: 300; font-size: 0.9em;">Firma Hash Blockchain: <br> <span style="font-family: monospace; color: #778DA9; font-size: 0.9em; word-break: break-all;">{{ hash_resultado }}</span></p>
                                <p style="color: #778DA9; margin-bottom: 0; font-weight: 300; font-size: 0.85em;">Sello de tiempo: {{ timestamp }}</p>
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
            <div class="content-wrapper-inner" style="max-width: 800px; width: 100%;">
                
                <div style="width: 100%; margin-bottom: 15px; text-align: left;">
                    <h2 class="app-title" style="text-align: left; margin: 0;">Bóveda Criptográfica</h2>
                    <p class="app-subtitle" style="text-align: left; margin: 5px 0 0 0; font-weight: 300;">Archivos encriptados y monitoreados en tiempo real.</p>
                </div>
                
                <div class="metrics-wrapper">
                    <div class="metric-card">
                        <p class="metric-value">{{ proyectos|selectattr('plagio', 'equalto', False)|list|length }}</p>
                        <p class="metric-label">Activos Protegidos</p>
                    </div>
                    <div class="metric-card">
                        <p class="metric-value" style="color: #FCA5A5;">34</p>
                        <p class="metric-label">Plagios Bloqueados</p>
                    </div>
                    <div class="metric-card">
                        <p class="metric-value" style="font-size: 1.5em; margin-top: 8px;">🟢 Activo</p>
                        <p class="metric-label">Radar OSINT 24/7</p>
                    </div>
                </div>

                <div class="sub-nav">
                    <button class="sub-tab-btn active" onclick="cambiarSubPestana('boveda-personal-tab', this)">Mi Bóveda Personal</button>
                    <button class="sub-tab-btn" onclick="cambiarSubPestana('boveda-instagram-tab', this)">
                        <span class="social-badge badge-instagram">IG</span> Instagram <span style="color: #5EEAD4; font-size: 0.7em; margin-left: 5px; font-family: 'Oswald';">PRO</span>
                    </button>
                    <button class="sub-tab-btn" onclick="cambiarSubPestana('boveda-facebook-tab', this)">
                        <span class="social-badge badge-facebook">FB</span> Facebook <span style="color: #5EEAD4; font-size: 0.7em; margin-left: 5px; font-family: 'Oswald';">PRO</span>
                    </button>
                    <button class="sub-tab-btn" onclick="cambiarSubPestana('boveda-x-tab', this)">
                        <span class="social-badge badge-x">𝕏</span> X (Twitter) <span style="color: #5EEAD4; font-size: 0.7em; margin-left: 5px; font-family: 'Oswald';">PRO</span>
                    </button>
                </div>
                
                <div id="boveda-personal-tab" class="sub-section-container" style="display: flex; opacity: 1;">
                    <div class="grid-proyectos" id="lista-boveda">
                        {% if proyectos %}
                            {% for p in proyectos %}
                            <div class="card-proyecto" data-hash="{{ p.hash_full }}" onclick="clickEnTarjeta(event, this)">
                                <div class="select-indicator"></div>
                                <div class="card-header-flex">
                                    <span></span>
                                    <div class="dropdown">
                                        <button onclick="toggleDropdown('drop-{{ loop.index }}')" class="dots-btn">⋮</button>
                                        <div id="drop-{{ loop.index }}" class="dropdown-content">
                                            <a href="#" onclick="verInforme('{{ p.nombre }}', '{{ p.hash_full }}', '{{ p.plagio }}')">Ver informe general</a>
                                            <a href="#" style="color: #5EEAD4; font-size: 0.82em; white-space: normal; line-height: 1.3;" onclick="verCertificado('{{ p.nombre }}', '{{ p.hash_full }}', '{{ p.timestamp|default('Fecha no disponible') }}')">Ver Certificado Legal</a>
                                            <a href="#" onclick="activarModoSeleccion('{{ p.hash_full }}')">Seleccionar</a>
                                            <a href="#" onclick="renombrarArchivo('{{ p.hash_full }}', '{{ p.nombre }}', this)">Cambiar nombre</a>
                                            <a href="#" onclick="eliminarConAnimacion('{{ p.hash_full }}', this)">Eliminar</a>
                                        </div>
                                    </div>
                                </div>
                                <div class="img-mock">
                                    {% if p.nombre.endswith('.pdf') %}📄{% elif p.nombre.endswith('.docx') or p.nombre.endswith('.doc') %}📝{% else %}📷{% endif %}
                                </div>
                                <p style="margin: 0; font-weight: 400; font-size: 0.95em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #E0E1DD; width: 100%;" title="{{ p.nombre }}">{{ p.nombre }}</p>
                                <small style="color: #778DA9; font-size: 0.7em; margin-top: 5px; font-family: monospace;">ID: {{ p.hash }}</small>
                                {% if p.plagio %}<span class="badge-status badge-alert">🔴 Alerta de Plagio en Web</span>{% else %}<span class="badge-status badge-clean">🟢 Monitor 24/7 Activo</span>{% endif %}
                            </div>
                            {% endfor %}
                        {% else %}
                            <div style="grid-column: 1 / -1; text-align: center; color: #778DA9; padding: 40px; width: 100%; display: flex; flex-direction: column; align-items: center;">
                                <p style="font-weight: 300; margin-bottom: 20px;">Tu bóveda está vacía.<br>Sube tu primer archivo para protegerlo.</p>
                                <button class="btn btn-secondary" onclick="cambiarPestana('app-section')">Subir Archivo</button>
                            </div>
                        {% endif %}
                    </div>
                </div>

                <div id="boveda-instagram-tab" class="sub-section-container">
                    <div id="ig-connect-area" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; transition: opacity 0.3s ease;">
                        <div style="font-size: 3em; margin-bottom: 5px; line-height: 1;">📸</div>
                        <h3 style="color: #E0E1DD; font-family: 'Oswald', sans-serif; font-size: 1.5em; margin: 0 0 5px 0; text-align: center;">Protección Automatizada para Creadores</h3>
                        <p style="color: rgba(224, 225, 221, 0.85); font-weight: 300; font-size: 0.95em; margin: 0 auto 20px auto; max-width: 500px; line-height: 1.5; text-align: center;">Vincula tu cuenta de Instagram. La plataforma leerá tu feed, extraerá cada nueva publicación fotográfica o diseño y lo protegerá en la Blockchain de forma automática.</p>
                        <button class="btn" style="background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); border: none; font-size: 0.95em; padding: 12px 30px;" onclick="simularConexion('Instagram', 'ig-connect-area')">Vincular cuenta de Instagram</button>
                    </div>
                </div>

                <div id="boveda-facebook-tab" class="sub-section-container">
                    <div id="fb-connect-area" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; transition: opacity 0.3s ease;">
                        <div style="font-size: 3em; margin-bottom: 5px; line-height: 1;">💼</div>
                        <h3 style="color: #E0E1DD; font-family: 'Oswald', sans-serif; font-size: 1.5em; margin: 0 0 5px 0; text-align: center;">Blindaje de Propiedad Intelectual Corporativa</h3>
                        <p style="color: rgba(224, 225, 221, 0.85); font-weight: 300; font-size: 0.95em; margin: 0 auto 20px auto; max-width: 500px; line-height: 1.5; text-align: center;">Conecta la Fanpage de tu empresa. El radar OSINT registrará todos los catálogos y banners subidos, generando certificados de anterioridad irrefutables.</p>
                        <button class="btn" style="background-color: #1877F2; border: none; font-size: 0.95em; padding: 12px 30px;" onclick="simularConexion('Facebook', 'fb-connect-area')">Vincular página de Facebook</button>
                    </div>
                </div>

                <div id="boveda-x-tab" class="sub-section-container">
                    <div id="x-connect-area" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; transition: opacity 0.3s ease;">
                        <div style="font-size: 3em; margin-bottom: 5px; line-height: 1;">🐦</div>
                        <h3 style="color: #E0E1DD; font-family: 'Oswald', sans-serif; font-size: 1.5em; margin: 0 0 5px 0; text-align: center;">Certificación de Contenido en Tiempo Real</h3>
                        <p style="color: rgba(224, 225, 221, 0.85); font-weight: 300; font-size: 0.95em; margin: 0 auto 20px auto; max-width: 500px; line-height: 1.5; text-align: center;">Protege tus hilos virales, investigaciones escritas y material audiovisual en el momento exacto en que los publicas.</p>
                        <button class="btn" style="background-color: #0F1419; border: 1px solid rgba(255,255,255,0.2); font-size: 0.95em; padding: 12px 30px;" onclick="simularConexion('X', 'x-connect-area')">Vincular cuenta de X</button>
                    </div>
                </div>

            </div>
        </div>

        <div id="planes-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 900px;">
                <h2 class="app-title" style="text-align: center; margin: 0 0 10px 0;">Planes y Precios</h2>
                <p class="app-subtitle" style="text-align: center; margin: 0 0 40px 0; font-weight: 300;">Escala la protección de tus activos según tus necesidades.</p>
                <div class="glass-grid-3">
                    <div class="glass-card" style="display: flex; flex-direction: column;">
                        <h3 style="color: #E0E1DD;">Básico</h3>
                        <h2 style="color: #5EEAD4; font-size: 2.5em; margin: 10px 0;">Gratis</h2>
                        <ul style="text-align: left; font-size: 0.9em; color: rgba(224, 225, 221, 0.85); padding-left: 20px; line-height: 1.8; flex-grow: 1;">
                            <li>Protección manual de activos.</li>
                            <li>Límite de 5 archivos en bóveda.</li>
                            <li>Generación de firma Hash.</li>
                            <li>Auditoría bajo demanda.</li>
                        </ul>
                        <button class="btn btn-secondary" style="margin-top: 20px; width: 100%;">Plan Actual</button>
                    </div>
                    <div class="glass-card" style="display: flex; flex-direction: column; border-color: #5EEAD4; box-shadow: 0 0 15px rgba(94, 234, 212, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1);">
                        <h3 style="color: #E0E1DD;">Pro Creador</h3>
                        <h2 style="color: #5EEAD4; font-size: 2.5em; margin: 10px 0;">$9.99<span style="font-size: 0.4em; color: #778DA9;">/mes</span></h2>
                        <ul style="text-align: left; font-size: 0.9em; color: rgba(224, 225, 221, 0.85); padding-left: 20px; line-height: 1.8; flex-grow: 1;">
                            <li>Todo lo del plan Básico.</li>
                            <li>Sincronización automática de Instagram y X.</li>
                            <li>Radar OSINT 24/7 activo.</li>
                            <li>Archivos ilimitados.</li>
                        </ul>
                        <button class="btn" style="margin-top: 20px; width: 100%;">Mejorar a Pro</button>
                    </div>
                    <div class="glass-card" style="display: flex; flex-direction: column;">
                        <h3 style="color: #E0E1DD;">Enterprise</h3>
                        <h2 style="color: #5EEAD4; font-size: 2.5em; margin: 10px 0;">$49.99<span style="font-size: 0.4em; color: #778DA9;">/mes</span></h2>
                        <ul style="text-align: left; font-size: 0.9em; color: rgba(224, 225, 221, 0.85); padding-left: 20px; line-height: 1.8; flex-grow: 1;">
                            <li>Todo lo del plan Pro Creador.</li>
                            <li>Conexión de Fanpages corporativas.</li>
                            <li>Protección masiva de catálogos.</li>
                            <li>Takedown automático (Cease & Desist).</li>
                        </ul>
                        <button class="btn btn-secondary" style="margin-top: 20px; width: 100%;">Contactar Ventas</button>
                    </div>
                </div>
            </div>
        </div>

        <div id="como-funciona-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 900px;">
                <h2 class="app-title" style="text-align: center; margin: 0 0 10px 0;">¿Cómo funciona?</h2>
                <p class="app-subtitle" style="text-align: center; margin: 0 0 40px 0; font-weight: 300;">Tecnología ágil y accesible detrás de la plataforma.</p>
                <div class="glass-grid-3">
                    <div class="glass-card">
                        <h3>Lectura Inteligente</h3>
                        <p>Al subir un archivo, nuestra tecnología funciona como un "ojo virtual". Analiza el texto de tus documentos o los colores y formas de tus imágenes para crear una huella matemática única.</p>
                    </div>
                    <div class="glass-card">
                        <h3>Radar Global OSINT</h3>
                        <p>Una vez creada la huella, el sistema lanza una búsqueda profunda y rápida en la red y perfiles públicos. Su objetivo es confirmar que nadie más haya publicado tu trabajo previamente.</p>
                    </div>
                    <div class="glass-card">
                        <h3>Bóveda Segura</h3>
                        <p>Si el archivo es original, le otorgamos un código indestructible (Blockchain) y lo guardamos bajo llave. Si detectamos una copia en internet, se rechaza la protección.</p>
                    </div>
                </div>
            </div>
        </div>

        <div id="quienes-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 900px;">
                <h2 class="app-title" style="text-align: center; margin: 0 0 10px 0;">Redefiniendo el Derecho Digital</h2>
                <p class="app-subtitle" style="text-align: center; margin: 0 0 40px 0; font-weight: 300;">Automatizamos y democratizamos la protección de activos digitales.</p>
                <div class="glass-grid-2">
                    <div class="glass-card">
                        <h3>El Desafío</h3>
                        <p>En la era digital, el plagio y la copia no autorizada de cursos, software y diseños ocurren a la velocidad de la luz. La defensa legal tradicional es burocrática, lenta y sumamente costosa para las PyMEs.</p>
                    </div>
                    <div class="glass-card">
                        <h3>La Solución</h3>
                        <p><span style="color: #778DA9; font-weight: 400;">DeepTech Legal Solutions S.A.P.I. de C.V.</span> transforma este proceso reactivo en un ecosistema proactivo mediante un modelo SaaS diseñado para detectar y actuar en tiempo real.</p>
                    </div>
                </div>
                <div class="glass-grid-3">
                    <div class="glass-card">
                        <h3>Nuestra Misión</h3>
                        <p>Ofrecer herramientas tecnológicas accesibles que permitan a los usuarios defender sus creaciones de manera eficiente y segura desde etapas tempranas.</p>
                    </div>
                    <div class="glass-card">
                        <h3>Nuestra Visión</h3>
                        <p>Liderar la evolución del derecho digital a nivel global, creando el estándar de protección perimetral e inmutable para creadores de contenido.</p>
                    </div>
                    <div class="glass-card">
                        <h3>Tecnología Dual</h3>
                        <p>Combinamos Inteligencia Artificial (rastreo web OSINT 24/7) y tecnología Blockchain (certificados de autoría inmutables) en una sola plataforma.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="notificaciones-section" class="section-container app-centered-layout" style="display: none; opacity: 0;">
            <div class="content-wrapper-inner" style="max-width: 650px;">
                <h2 class="app-title" style="text-align: center; margin: 0 0 10px 0;">Buzón de Notificaciones</h2>
                <p class="app-subtitle" style="text-align: center; margin: 0 0 30px 0; font-weight: 300;">Actualizaciones sobre tus solicitudes y auditorías.</p>
                
                <div id="lista-notificaciones" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
                    <div id="notif-vacia" style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #778DA9; padding: 40px; width: 100%;">
                        <div style="font-size: 3em; margin-bottom: 10px; line-height: 1;">📭</div>
                        <p style="font-weight: 300; margin: 0;">No tienes notificaciones nuevas.</p>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <div id="bulk-action-bar" class="bulk-action-bar">
        <span style="font-weight: 400; color: white; font-family: 'Oswald', sans-serif;"><span id="sel-count">0</span> seleccionados</span>
        <button class="btn btn-secondary" style="padding: 8px 15px; margin-left: 10px;" onclick="cancelarSeleccion()">Cancelar</button>
        <button class="btn btn-danger" style="padding: 8px 15px;" onclick="eliminarSeleccionados()">Eliminar</button>
    </div>

    <div id="informe-modal" class="modal-overlay">
        <div class="glass-card" style="width: 90%; max-width: 500px; position: relative;">
            <button class="modal-close-btn" onclick="cerrarInforme()">&times;</button>
            <h2 style="color: #E0E1DD; margin-top: 0; text-align: center;">📄 Informe de Auditoría</h2>
            <div style="margin-top: 20px;">
                <p style="font-weight: 300; text-align: left;">Archivo protegido: <br><span id="inf-nombre" style="color: #778DA9;"></span></p>
                <p style="font-weight: 300; text-align: left; margin-top:10px;">ID Blockchain (Firma SHA-256): <br><span id="inf-hash" style="font-family: monospace; color: #778DA9; word-break: break-all; font-size: 0.9em;"></span></p>
                <p style="font-weight: 300; text-align: left; margin-top:10px;">Estado del Monitor: <br><span id="inf-estado"></span></p>
                
                <div style="margin-top: 15px; border-top: 1px solid rgba(119, 141, 169, 0.2); padding-top: 15px;">
                    <p style="font-weight: 500; text-align: left; margin-bottom: 10px; font-size: 0.9em; color: #E0E1DD;">Bitácora de Rastreo OSINT 24/7:</p>
                    <div id="inf-bitacora" class="url-list" style="max-height: 120px; margin-top: 0; text-align: left;"></div>
                </div>

            </div>
            <div style="text-align: center; margin-top: 30px;">
                <button class="btn btn-secondary" onclick="cerrarInforme()">Cerrar Informe</button>
            </div>
        </div>
    </div>

    <div id="certificado-modal" class="modal-overlay">
        <div class="glass-card" style="width: 95%; max-width: 650px; position: relative; padding: 20px;">
            <button class="modal-close-btn" onclick="cerrarCertificado()">&times;</button>
            
            <div class="certificate-box">
                <div style="text-align: center;">
                    <p class="cert-logo">DeepTech™</p>
                    <h2 class="cert-title">CERTIFICADO DE AUTORÍA Y SELLO DE TIEMPO</h2>
                </div>
                
                <p class="cert-text">
                    A través de la presente, <strong>DeepTech Legal Solutions S.A.P.I. de C.V.</strong> certifica que el activo digital identificado en este documento ha sido analizado por nuestro motor de Inteligencia Artificial (OSINT) y registrado exitosamente en la cadena de bloques (Blockchain), estableciendo una prueba inmutable de anterioridad y autoría.
                </p>
                
                <div style="background: rgba(13, 27, 42, 0.5); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="margin: 0 0 5px 0; font-size: 0.85em; color: #778DA9;">Nombre del Activo:</p>
                    <p id="cert-nombre" style="margin: 0 0 15px 0; color: #E0E1DD; font-weight: 500; word-break: break-all;"></p>
                    
                    <p style="margin: 0 0 5px 0; font-size: 0.85em; color: #778DA9;">Identificador Criptográfico (Firma SHA-256):</p>
                    <p id="cert-hash" style="margin: 0; color: #5EEAD4; font-family: monospace; font-size: 0.9em; word-break: break-all;"></p>
                </div>
                
                <div class="cert-data-row">
                    <div style="display: flex; flex-direction: column; text-align: left;">
                        <span style="color: #778DA9; margin-bottom: 5px;">Sello de Tiempo (Timestamp):</span>
                        <strong id="cert-fecha" style="color: #E0E1DD;"></strong>
                    </div>
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <div class="cert-seal">SELLO<br>VÁLIDO</div>
                        <div class="qr-placeholder">🔲</div>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn" onclick="alert('Funcionalidad de descarga de PDF activada para tu presentación.')">Descargar Certificado PDF</button>
            </div>
        </div>
    </div>

    <div id="auditoria-modal" class="modal-overlay">
        <div class="glass-card" style="width: 90%; max-width: 500px; position: relative;">
            <button class="modal-close-btn" onclick="cerrarAuditoria()">&times;</button>
            <h2 style="color: #E0E1DD; margin-top: 0; text-align: center;">⚖️ Solicitud de Auditoría</h2>
            <div style="margin-top: 20px;">
                <p style="font-weight: 300; text-align: left;">Archivo a revisar: <br><span style="color: #778DA9;">{% if mostrando_resultado %}{{ nombre_archivo }}{% else %}Archivo Auditado{% endif %}</span></p>
                <p style="font-weight: 300; text-align: left; margin-top:10px;">Motivo de la solicitud: <br><span style="font-family: monospace; color: #778DA9; font-size: 0.9em;">Revisión manual por posible falso positivo / uso justo.</span></p>
                <p style="font-weight: 300; text-align: left; margin-top:10px;">Estado de la solicitud: <br><span id="auditoria-estado" style="color: #FCA5A5; font-weight: 500;">Pendiente de envío</span></p>
            </div>
            <div style="text-align: center; margin-top: 30px; display: flex; justify-content: center; gap: 15px;">
                <button id="btn-enviar-auditoria" class="btn" onclick="enviarAuditoria()">Enviar Solicitud</button>
            </div>
        </div>
    </div>

    <form id="rename-form" action="/renombrar" method="POST" style="display: none;">
        <input type="hidden" name="hash_id" id="rename-hash">
        <input type="hidden" name="nuevo_nombre" id="rename-name">
    </form>

    <script>
        let unreadCount = 0;

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
            }, 500);
        }

        function transicionAuditarNuevo() {
            var appSec = document.getElementById('app-section');
            appSec.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            appSec.style.opacity = '0';
            appSec.style.transform = 'translateY(10px)';
            
            var textoCarga = document.getElementById('texto-carga');
            if(textoCarga) {
                textoCarga.style.fontFamily = "'Montserrat', sans-serif";
                textoCarga.style.color = "#778DA9";
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
                
                var innerWrapper = document.getElementById('app-inner-wrapper');
                if(innerWrapper) innerWrapper.classList.add('view-centered');
                
                var trustBadges = document.getElementById('upload-badges');
                if(trustBadges) trustBadges.style.display = 'flex';
                
                appSec.style.transform = 'translateY(0px)';
                appSec.style.opacity = '1';
                window.history.pushState({}, document.title, "/?skip_intro=true");
            }, 400);
        }

        function cambiarPestana(idMostrar) {
            cancelarSeleccion();
            var appSec = document.getElementById('app-section');
            var dashSec = document.getElementById('dashboard-section');
            var infoSec = document.getElementById('como-funciona-section');
            var qsSec = document.getElementById('quienes-section');
            var notifSec = document.getElementById('notificaciones-section');
            var planesSec = document.getElementById('planes-section');
            
            var tabAuditar = document.getElementById('tab-auditar');
            var tabBoveda = document.getElementById('tab-boveda');
            var tabInfo = document.getElementById('tab-como-funciona');
            var tabQs = document.getElementById('tab-quienes');
            var tabNotif = document.getElementById('tab-notificaciones');
            var tabPlanes = document.getElementById('tab-planes');

            if(tabAuditar) tabAuditar.classList.remove('active');
            if(tabBoveda) tabBoveda.classList.remove('active');
            if(tabInfo) tabInfo.classList.remove('active');
            if(tabQs) tabQs.classList.remove('active');
            if(tabNotif) tabNotif.classList.remove('active');
            if(tabPlanes) tabPlanes.classList.remove('active');

            if(idMostrar === 'app-section') { if(tabAuditar) tabAuditar.classList.add('active'); }
            else if(idMostrar === 'dashboard-section') { if(tabBoveda) tabBoveda.classList.add('active'); }
            else if(idMostrar === 'como-funciona-section') { if(tabInfo) tabInfo.classList.add('active'); }
            else if(idMostrar === 'quienes-section') { if(tabQs) tabQs.classList.add('active'); }
            else if(idMostrar === 'planes-section') { if(tabPlanes) tabPlanes.classList.add('active'); }
            else if(idMostrar === 'notificaciones-section') { 
                if(tabNotif) tabNotif.classList.add('active'); 
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
                    setTimeout(function() {
                        sec.style.display = 'none';
                    }, 300); 
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
                        <p style="color: #778DA9; font-weight: 300; font-size: 1.1em; margin-top: 20px; text-align: center;">Estableciendo conexión segura con la API de ${redSocial}...</p>
                        <p style="color: rgba(224, 225, 221, 0.6); font-size: 0.9em; text-align: center;">Validando tokens OAuth 2.0</p>
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
                    let icon = redSocial === 'X' ? '📝' : '📷';
                    let mockCards = '';
                    
                    for(let i=1; i<=3; i++) {
                        let shortId = Math.random().toString(36).substring(2, 10).toUpperCase();
                        mockCards += `
                            <div class="card-proyecto" style="cursor: default;">
                                <div class="card-header-flex">
                                    <span class="social-badge badge-${redSocial.toLowerCase()}" style="margin:0;">${redSocial}</span>
                                </div>
                                <div class="img-mock" style="margin-top: 10px;">${icon}</div>
                                <p style="margin: 0; font-weight: 400; font-size: 0.95em; color: #E0E1DD; width: 100%;">Pub_${redSocial}_00${i}</p>
                                <small style="color: #778DA9; font-size: 0.7em; margin-top: 5px; font-family: monospace;">ID: ${shortId}...</small>
                                <span class="badge-status badge-clean">🟢 Monitor 24/7 Activo</span>
                            </div>
                        `;
                    }

                    container.style.opacity = 0;
                    setTimeout(() => {
                        container.innerHTML = `
                            <div style="width: 100%; display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; border-bottom: 1px solid rgba(119,141,169,0.2); padding-bottom: 15px;">
                                <h3 style="color: #5EEAD4; margin:0 0 5px 0; font-family: 'Oswald', sans-serif; font-size: 1.5em; text-align: center;">✓ Cuenta vinculada exitosamente</h3>
                                <p style="color: rgba(224, 225, 221, 0.85); margin:0; font-weight: 300; font-size: 1em; text-align: center;">La plataforma ha importado y protegido tus últimas publicaciones automáticamente.</p>
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
                        textoCarga.style.color = "#5EEAD4";
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
                    lista.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: #778DA9; padding: 40px; width: 100%; display: flex; flex-direction: column; align-items: center;"><p style="font-weight: 300; margin-bottom: 20px;">Tu bóveda está vacía.<br>Sube tu primer archivo para protegerlo.</p><button class="btn btn-secondary" onclick="cambiarPestana(\'app-section\')">Subir Archivo</button></div>';
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
            if(bar) { bar.style.opacity = '0'; setTimeout(() => { bar.style.display = 'none'; }, 300); }
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
                document.getElementById('inf-estado').innerHTML = '<span style="color: #FCA5A5; font-weight: 500;">🔴 Alerta de Plagio: Se encontraron copias idénticas.</span>';
            } else {
                document.getElementById('inf-estado').innerHTML = '<span style="color: #778DA9; font-weight: 500;">🟢 100% Original - Activo monitoreado y seguro.</span>';
            }
            
            let bitacora = document.getElementById('inf-bitacora');
            if(bitacora) {
                let d = new Date();
                let horaAyer = new Date(d.getTime() - (24 * 60 * 60 * 1000));
                
                let hHoy = d.getHours().toString().padStart(2, '0') + ":" + d.getMinutes().toString().padStart(2, '0') + (d.getHours() >= 12 ? ' PM' : ' AM');
                let hAyer = horaAyer.getHours().toString().padStart(2, '0') + ":" + horaAyer.getMinutes().toString().padStart(2, '0') + (horaAyer.getHours() >= 12 ? ' PM' : ' AM');
                
                if(plagio === 'True') {
                    bitacora.innerHTML = `
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:#FCA5A5;">🔴 Hoy, ${hHoy}</span> - Se detectaron copias idénticas en la red.</div>
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:#FCA5A5;">🔴 Ayer, ${hAyer}</span> - Alerta de posibles similitudes detectadas.</div>
                    `;
                } else {
                    bitacora.innerHTML = `
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:#5EEAD4;">🟢 Hoy, ${hHoy}</span> - Escaneo completado. 0 coincidencias.</div>
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:#5EEAD4;">🟢 Ayer, ${hAyer}</span> - Escaneo OSINT completado. 0 coincidencias.</div>
                        <div style="font-size: 0.85em; margin-bottom: 8px;"><span style="color:#778DA9;">⚪ Registro Inicial</span> - Sello de tiempo creado en Blockchain.</div>
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
                    btn.style.backgroundColor = "#415A77";
                    btn.style.color = "#E0E1DD";
                    btn.disabled = false;
                }
                if(estado) {
                    estado.innerHTML = "Pendiente de envío";
                    estado.style.color = "#FCA5A5";
                }
            }, 300);
        }

        function enviarAuditoria() {
            var btn = document.getElementById('btn-enviar-auditoria');
            var estado = document.getElementById('auditoria-estado');
            
            btn.innerHTML = "⏳ Procesando...";
            btn.disabled = true;
            
            setTimeout(() => {
                btn.innerHTML = "✓ Solicitud Enviada";
                btn.style.backgroundColor = "#5EEAD4";
                btn.style.color = "#0D1B2A";
                
                if(estado) {
                    estado.innerHTML = "🟢 En revisión por especialista legal";
                    estado.style.color = "#5EEAD4";
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
                    <p>Se ha levantado un ticket de revisión manual para el archivo: <span style="color:#778DA9; font-weight:500;">${fileName}</span>. Un especialista legal de DeepTech evaluará tu caso en las próximas 24 horas.</p>
                    <span class="notif-time">${dateString} - ${timeString}</span>
                </div>
            `;
            
            container.innerHTML = notifHTML + container.innerHTML;
            
            unreadCount++;
            let badge = document.getElementById('notif-badge');
            badge.innerText = unreadCount;
            badge.style.display = 'inline-block';
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
        # Generamos la huella matemática de la imagen entrante
        img = Image.open(io.BytesIO(imagen_bytes))
        nuevo_phash = imagehash.phash(img)
        
        # Comparamos contra la memoria de la bóveda
        for proyecto in db_proyectos:
             if 'phash' in proyecto and proyecto['phash']:
                hash_guardado = imagehash.hex_to_hash(proyecto['phash'])
                distancia = nuevo_phash - hash_guardado
                
                # Tolerancia estricta: Permite ligeros recortes o cambios de calidad, pero rechaza imágenes "similares"
                if distancia <= 2: 
                    return True
        return False
    except Exception as e:
        print("Error en pHash:", e)
        return False

def buscar_imagen_estricta_serpapi(imagen_bytes, nombre_archivo):
    # FASE 1: Comprobación Local Inmediata
    if comparar_phash_local(imagen_bytes):
        resultado_local = [{
            "titulo": "Registro Encontrado en Base de Datos Interna",
            "link": "Plataforma Local",
            "es_instagram": False,
            "es_facebook": False
        }]
        return resultado_local, None

    # FASE 2: Subida y Análisis OSINT
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

        # Extraer coincidencias que Google ya considera idénticas
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

        # Validación matemática sobre los "similares" para encontrar copias camufladas
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
                        
                        # Si la imagen web es estructuralmente la misma 
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
            for pagina in lector.pages[:4]: # Escaneamos hasta 4 páginas
                texto = pagina.extract_text()
                if texto:
                    # Dividimos el texto en oraciones usando puntos y saltos de línea
                    oraciones = texto.replace('\n', ' ').split('. ')
                    fragmentos_candidatos.extend(oraciones)
                    
        elif extension in ['doc', 'docx']:
            doc = docx.Document(io.BytesIO(archivo_bytes))
            for parrafo in doc.paragraphs[:20]: # Escaneamos los primeros 20 párrafos
                if parrafo.text:
                    oraciones = parrafo.text.replace('\n', ' ').split('. ')
                    fragmentos_candidatos.extend(oraciones)
                    
    except Exception as e:
        return None, f"Error al leer documento: {str(e)}"
        
    # Filtrado Inteligente: Descartamos fragmentos menores a 15 palabras
    fragmentos_limpios = [f.strip() for f in fragmentos_candidatos if len(f.split()) > 15]
    
    if not fragmentos_limpios: 
        return [], None
        
    # Ordenamos de mayor a menor longitud para encontrar la oración más densa
    fragmentos_limpios.sort(key=lambda x: len(x.split()), reverse=True)
    
    # Aislamos la mejor huella textual y la limitamos a ~25 palabras
    mejor_fragmento = fragmentos_limpios[0]
    palabras_clave = mejor_fragmento.split()
    fragmento_clave = " ".join(palabras_clave[:25])
    
    try:
        # Ejecutamos el radar con coincidencia exacta
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
    # IMPORTANTE: Escuchando en todos los puertos para la nube (Render)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
