#!/usr/bin/env python3
"""
Gang Empire Finder - Herramienta para buscar usuarios en múltiples bases de datos JSON,
comprobar cuentas premium de Minecraft y romper hashes de contraseñas usando todos los diccionarios disponibles.
"""

import os
import json
import hashlib
import argparse
import time
import base64
import binascii
import requests
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple, Union
import http.server
import socketserver
import webbrowser
import urllib.parse
import sys
try:
    from tqdm import tqdm
except ImportError:
   
    def tqdm(iterable, *args, **kwargs):
        total = len(iterable) if hasattr(iterable, '__len__') else None
        prefix = kwargs.get('desc', '')
        if total:
            print(f"{prefix} - Procesando {total} elementos...")
        return iterable

try:
    from pypresence import Presence
    DISCORD_RPC_AVAILABLE = True
except ImportError:
    DISCORD_RPC_AVAILABLE = False


DATA_DIR = Path(r"C:\Users\Darks\Desktop\Gang`s Empire Finder\data")
WORDLISTS_DIR = Path(r"C:\Users\Darks\Desktop\Gang`s Empire Finder\wordlists")
WEB_DIR = Path(r"C:\Users\Darks\Desktop\Gang`s Empire Finder\web")


DISCORD_CLIENT_ID = "1370056983666757673"  


HASH_TYPES = {
    "md5": {"func": hashlib.md5, "len": 32},
    "sha1": {"func": hashlib.sha1, "len": 40},
    "sha256": {"func": hashlib.sha256, "len": 64},
    "sha512": {"func": hashlib.sha512, "len": 128}
}


users_data = {}
wordlists = {}
results_cache = {}
premium_cache = {}  # Cache para el estado premium de las cuentas

class DiscordRPC:
    """Maneja la integración con Discord Rich Presence."""
    
    def __init__(self):
        self.rpc = None
        self.connected = False
        
        if DISCORD_RPC_AVAILABLE:
            try:
                self.rpc = Presence(DISCORD_CLIENT_ID)
                self.rpc.connect()
                self.connected = True
                print("Discord RPC conectado correctamente.☠")
                
                
                self.update_presence("🔍 Localizando jugador...")
            except Exception as e:
                print(f"Error al conectar con Discord RPC: {e}")
    
    def update_presence(self, details, state="🔥 EL MEJOR FINDER DE MINECRAFT DEL MUNDO 🔥", large_image="gang`s empire finder"):
        """Actualiza la información mostrada en Discord."""
        if not self.connected:
            return
        
        try:
            self.rpc.update(
                details=details,
                state=state,
                large_image=large_image,  
                large_text="🔥 EL MEJOR FINDER DE MINECRAFT DEL MUNDO 🔥",
                start=int(time.time())
            )
        except Exception as e:
            print(f"Error al actualizar Discord RPC: {e}")

class HashCracker:
    """Clase para romper hashes de contraseñas usando diccionarios."""
    
    @staticmethod
    def identify_hash_type(hash_str: str) -> Optional[str]:
        """Identifica el tipo de hash basado en su longitud."""
        hash_str = hash_str.lower()
        
        if hash_str.startswith('$'):
            parts = hash_str.split('$')
            if len(parts) >= 3:
                if parts[1] == '2y' or parts[1] == '2a' or parts[1] == '2b':
                    return "bcrypt"
                elif parts[1] == '1' or parts[1] == '5' or parts[1] == '6':
                    return "sha" + parts[1]
                elif parts[1] == 'sha1':
                    return "sha1"
                elif parts[1] == 'sha256':
                    return "sha256"
                elif parts[1] == 'sha512':
                    return "sha512"
                elif parts[1] == 'md5':
                    return "md5"
        
        
        str_len = len(hash_str)
        for hash_type, info in HASH_TYPES.items():
            if str_len == info["len"]:
                return hash_type
                
        
        try:
            int(hash_str, 16)
            
            if str_len == 16:
                return "md5-half"
            elif str_len > 24:  
                return "unknown"
        except ValueError:
            
            if hash_str.endswith("==") or hash_str.endswith("="):
                try:
                    base64.b64decode(hash_str)
                    return "base64"
                except:
                    pass
        
        return "unknown"
    
    @staticmethod
    def hash_password(password: str, hash_type: str, salt: str = "") -> str:
        """Genera un hash de la contraseña según el tipo especificado."""
        if hash_type not in HASH_TYPES:
            return None
        
        
        if salt:
            password_bytes = (password + salt).encode('utf-8')
        else:
            password_bytes = password.encode('utf-8')
        
       
        hash_func = HASH_TYPES[hash_type]["func"]
        hash_obj = hash_func(password_bytes)
        return hash_obj.hexdigest()
    
    @staticmethod
    def crack_hash_with_all_wordlists(hash_str: str, salt: str = "") -> Optional[Tuple[str, str]]:
        """Intenta romper un hash utilizando todos los diccionarios disponibles."""
        if not WORDLISTS_DIR.exists():
            print("Directorio de diccionarios no encontrado.")
            return None
        
        # Verificar qué diccionarios están disponibles
        wordlist_files = list(WORDLISTS_DIR.glob("*"))
        if not wordlist_files:
            print("No se encontraron diccionarios. Asegúrate de añadir algunos en la carpeta 'wordlists'.")
            return None
        
        hash_type = HashCracker.identify_hash_type(hash_str)
        if hash_type == "unknown" or hash_type not in HASH_TYPES:
            return None
        
        print(f"🕵️ Detectado hash tipo: {hash_type}")
        print(f"🔄 Probando {len(wordlist_files)} diccionarios disponibles...")
        
        # Intentar con cada diccionario
        for wordlist_path in tqdm(wordlist_files, desc="Probando diccionarios"):
            wordlist_name = wordlist_path.name
            result = HashCracker.crack_hash(hash_str, salt, wordlist_name)
            if result:
                return (result, wordlist_name)
        
        return None
    
    @staticmethod
    def crack_hash(hash_str: str, salt: str = "", wordlist_name: str = "rockyou.txt") -> Optional[str]:
        """🕶️ Iniciando secuencia: Intentando romper un hash mediante diccionario..."""
        
        cache_key = f"{hash_str}:{salt}:{wordlist_name}"
        if cache_key in results_cache:
            return results_cache[cache_key]
        
        
        hash_type = HashCracker.identify_hash_type(hash_str)
        if hash_type == "unknown" or hash_type not in HASH_TYPES:
            return None
        
        
        if wordlist_name not in wordlists:
            wordlist_path = WORDLISTS_DIR / wordlist_name
            if not wordlist_path.exists():
                print(f"Diccionario {wordlist_name} no encontrado.")
                return None
            
           
            try:
                with open(wordlist_path, 'r', encoding='latin-1', errors='ignore') as f:
                    wordlists[wordlist_name] = [line.strip() for line in f]
                print(f"Diccionario {wordlist_name} cargado con {len(wordlists[wordlist_name])} palabras.")
            except Exception as e:
                print(f"Error al cargar diccionario {wordlist_name}: {e}")
                return None
        
       
        total_words = len(wordlists[wordlist_name])
        print(f"🕶️ Intentando romper hash {hash_str[:10]}... ({hash_type}) con {total_words} palabras de {wordlist_name}...")
        
        for word in tqdm(wordlists[wordlist_name], desc=f"Rompiendo {hash_type} con {wordlist_name}"):
            hashed = HashCracker.hash_password(word, hash_type, salt)
            if hashed and hashed.lower() == hash_str.lower():
                results_cache[cache_key] = word
                return word
        
        
        results_cache[cache_key] = None
        return None

class MinecraftPremiumChecker:
    """Clase para verificar si una cuenta de Minecraft es premium."""
    
    @staticmethod
    def check_premium_status(username: str) -> Dict[str, Any]:
        """Verifica si un nombre de usuario de Minecraft corresponde a una cuenta premium."""
        
        # Comprobar si ya tenemos la información en caché
        if username in premium_cache:
            return premium_cache[username]
        
        try:
            # Intentar consultar la API de Mojang para verificar el estado premium
            url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
            response = requests.get(url, timeout=5)
            
            result = {
                "is_premium": False,
                "uuid": None,
                "info": {}
            }
            
            if response.status_code == 200:
                data = response.json()
                result["is_premium"] = True
                result["uuid"] = data.get("id")
                result["info"] = data
                
                # Obtener información adicional si está disponible
                try:
                    uuid = data.get("id")
                    if uuid:
                        profile_url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
                        profile_response = requests.get(profile_url, timeout=5)
                        if profile_response.status_code == 200:
                            profile_data = profile_response.json()
                            result["profile"] = profile_data
                except Exception as e:
                    print(f"Error al obtener perfil detallado: {e}")
            
            # Imprimir información de depuración
            print(f"DEBUG - API Response status: {response.status_code}")
            print(f"DEBUG - Premium result: {result['is_premium']}")
            
            # Guardar en caché para futuras consultas
            premium_cache[username] = result
            return result
            
        except Exception as e:
            print(f"Error al verificar estado premium: {e}")
            # Imprimir información detallada para depuración
            import traceback
            traceback.print_exc()
            return {"is_premium": False, "uuid": None, "error": str(e)}

class UserFinder:
    """Clase principal para buscar y procesar información de usuarios."""
 
    def __init__(self, discord_rpc=None):
        """Inicializa el buscador de usuarios."""
        self.discord_rpc = discord_rpc
        self.ensure_directories()
        self.load_databases()
    
    def add_user_data(self, username, data, source):
        username = username.lower()
        if username not in users_data:
            users_data[username] = []
        enriched_data = data.copy()
        enriched_data['source'] = source
        users_data[username].append(enriched_data)

    def ensure_directories(self):
        """Asegura que existan los directorios necesarios."""
        for directory in [DATA_DIR, WORDLISTS_DIR, WEB_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            
        
        html_file = WEB_DIR / "index.html"
        if not html_file.exists():
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Gang Empire Finder</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Courier New', monospace; 
            margin: 0; 
            padding: 0; 
            background: #000000; 
            color: #ff0000;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        h1 { 
            color: #ff0000; 
            text-shadow: 0 0 5px #ff0000;
            text-align: center;
            font-size: 36px;
        }
        .search-box { 
            margin: 20px 0; 
            padding: 20px; 
            background: #121212; 
            border-radius: 5px; 
            box-shadow: 0 0 10px rgba(255,0,0,0.5); 
            border: 1px solid #ff0000;
        }
        .input-group { 
            margin-bottom: 15px; 
        }
        input, select { 
            padding: 10px; 
            font-size: 16px; 
            border: 1px solid #ff0000; 
            border-radius: 4px; 
            background-color: #000000;
            color: #ff0000;
            font-family: 'Courier New', monospace;
        }
        button { 
            padding: 10px; 
            font-size: 16px;
            background: #440000; 
            color: #ff0000; 
            cursor: pointer; 
            border: 1px solid #ff0000; 
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            text-shadow: 0 0 5px #ff0000;
        }
        button:hover { 
            background: #660000; 
            box-shadow: 0 0 15px rgba(255,0,0,0.7);
        }
        .results { 
            margin-top: 20px; 
        }
        .user-card { 
            background: #121212; 
            margin-bottom: 15px; 
            padding: 15px; 
            border-radius: 5px; 
            box-shadow: 0 0 10px rgba(255,0,0,0.5); 
            border: 1px solid #ff0000;
        }
        .user-info { 
            margin-bottom: 10px; 
        }
        .source { 
            color: #ff6666; 
            font-size: 12px; 
        }
        .password-crack { 
            background: #220000; 
            padding: 10px; 
            margin-top: 10px; 
            border-left: 4px solid #ff0000; 
        }
        .premium-badge {
            background-color: #006600;
            color: #00ff00;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
            display: inline-block;
            margin-right: 10px;
            text-shadow: 0 0 3px #00ff00;
            animation: glow 1.5s infinite alternate;
        }
        .non-premium-badge {
            background-color: #660000;
            color: #ff0000;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes glow {
            from {
                box-shadow: 0 0 5px #00ff00;
            }
            to {
                box-shadow: 0 0 15px #00ff00;
            }
        }
        pre { 
            white-space: pre-wrap; 
            word-wrap: break-word; 
        }
        .logo {
            text-align: center;
            font-size: 24px;
            margin-bottom: 20px;
            color: #ff0000;
            text-shadow: 0 0 10px #ff0000;
        }
        .flame {
            color: #ff0000;
            text-shadow: 0 0 10px #ff0000;
            animation: flicker 1s infinite;
        }
        @keyframes flicker {
            0% { text-shadow: 0 0 5px #ff0000; }
            50% { text-shadow: 0 0 15px #ff0000, 0 0 20px #ff6600; }
            100% { text-shadow: 0 0 5px #ff0000; }
        }
        ::-webkit-scrollbar {
            width: 10px;
            background: #000000;
        }
        ::-webkit-scrollbar-thumb {
            background: #ff0000;
            border-radius: 5px;
        }
        .options-toggle {
            color: #ff6666;
            text-decoration: underline;
            cursor: pointer;
            margin-bottom: 10px;
            display: block;
        }
        .advanced-options {
            display: none;
            padding: 10px;
            background: #1a0000;
            margin-bottom: 15px;
            border-radius: 5px;
        }
        .checkbox-container {
            margin-bottom: 10px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            font-size: 18px;
            color: #ff0000;
        }
        .loading:after {
            content: '.';
            animation: dots 1.5s steps(5, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60% { content: '...'; }
            80%, 100% { content: ''; }
        }
        /* Nuevos estilos para ayudar con la depuración */
        .debug-info {
            background: #220022;
            padding: 10px;
            margin-top: 10px;
            border-left: 4px solid #ff00ff;
            font-size: 12px;
            color: #ff88ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Gang Empire Finder Premium</h1>
        <div class="logo">
            <span class="flame">🔥</span> EL MEJOR FINDER DE MINECRAFT DEL MUNDO <span class="flame">🔥</span>
        </div>
        <div class="search-box">
            <form id="search-form">
                <div class="input-group">
                    <input type="text" id="username" placeholder="Nombre de usuario a buscar" required>
                    <button type="submit">BUSCAR</button>
                </div>
                
                <span class="options-toggle" onclick="toggleOptions()">Opciones avanzadas ▼</span>
                
                <div id="advanced-options" class="advanced-options">
                    <div class="checkbox-container">
                        <input type="checkbox" id="check-premium" checked>
                        <label for="check-premium">Verificar cuenta premium</label>
                    </div>
                    
                    <div class="checkbox-container">
                        <input type="checkbox" id="crack-passwords" checked>
                        <label for="crack-passwords">Intentar descifrar contraseñas (todos los diccionarios)</label>
                    </div>
                </div>
            </form>
        </div>
        <div id="results" class="results"></div>
    </div>
    
    <script>
        function toggleOptions() {
            const options = document.getElementById('advanced-options');
            if (options.style.display === 'block') {
                options.style.display = 'none';
                document.querySelector('.options-toggle').textContent = 'Opciones avanzadas ▼';
            } else {
                options.style.display = 'block';
                document.querySelector('.options-toggle').textContent = 'Opciones avanzadas ▲';
            }
        }
        
        document.getElementById('search-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const checkPremium = document.getElementById('check-premium').checked;
            const crackPasswords = document.getElementById('crack-passwords').checked;
            
            document.getElementById('results').innerHTML = '<div class="loading">Buscando información para: ' + username + '</div>';
            
            // Hacer solicitud al servidor
            const url = '/search?username=' + encodeURIComponent(username) + 
                        '&check_premium=' + encodeURIComponent(checkPremium) + 
                        '&crack_passwords=' + encodeURIComponent(crackPasswords);
                        
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    console.log("Datos recibidos:", data); // Depuración en consola
                    displayResults(data, username);
                })
                .catch(error => {
                    document.getElementById('results').innerHTML = '<p>Error al buscar: ' + error + '</p>';
                    console.error("Error en la búsqueda:", error); // Depuración en consola
                });
        });
        
        function displayResults(data, username) {
            const resultsDiv = document.getElementById('results');
            console.log("Procesando resultados:", JSON.stringify(data)); // Más depuración
            
            if ((!data.results || data.results.length === 0) && (!data.premium_info || data.premium_info === null)) {
                resultsDiv.innerHTML = '<p>No se encontró información para: ' + username + '</p>';
                return;
            }
            
            let html = '<h2>Resultados para: ' + username + '</h2>';
            
            // Para depuración, mostrar toda la respuesta JSON
            html += '<div class="debug-info"><strong>DEBUG - Datos recibidos:</strong> <pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
            
            // Mostrar información de cuenta premium si existe
            if (data.premium_info) {
                html += '<div class="user-card">';
                html += '<h3>ESTADO DE CUENTA MINECRAFT</h3>';
                
                if (data.premium_info.is_premium === true) {
                    html += '<div class="premium-badge">CUENTA PREMIUM</div>';
                    if (data.premium_info.uuid) {
                        html += '<p><strong>UUID:</strong> ' + data.premium_info.uuid + '</p>';
                    }
                    // Mostrar más información del perfil si está disponible
                    if (data.premium_info.profile) {
                        const profile = data.premium_info.profile;
                        if (profile.properties) {
                            profile.properties.forEach(prop => {
                                if (prop.name === "textures") {
                                    try {
                                        const textureData = JSON.parse(atob(prop.value));
                                        if (textureData.textures && textureData.textures.SKIN && textureData.textures.SKIN.url) {
                                            html += '<p><strong>Skin URL:</strong> <a href="' + textureData.textures.SKIN.url + '" target="_blank">' + textureData.textures.SKIN.url + '</a></p>';
                                        }
                                    } catch(e) {
                                        console.error("Error parsing texture data:", e);
                                    }
                                }
                            });
                        }
                    }
                } else {
                    html += '<div class="non-premium-badge">CUENTA NO PREMIUM</div>';
                }
                
                // Si hay un error, mostrarlo
                if (data.premium_info.error) {
                    html += '<p><strong>Error:</strong> ' + data.premium_info.error + '</p>';
                }
                
                html += '</div>';
            }
            
            // Mostrar resultados de bases de datos
            if (data.results && data.results.length > 0) {
                html += '<h3>INFORMACIÓN DE BASES DE DATOS</h3>';
                data.results.forEach(result => {
                    html += '<div class="user-card">';
                    html += '<div class="user-info">';
                    
                    // Mostrar toda la información disponible
                    for (const [key, value] of Object.entries(result.data)) {
                        if (key !== 'source') {
                            html += '<p><strong>' + key + ':</strong> ';
                            
                            // Formato especial para contraseñas crackeadas
                            if (key === 'password' && result.cracked_password) {
                                html += value + '</p>';
                                html += '<div class="password-crack">';
                                html += '<p><strong>¡Contraseña descifrada!</strong> ' + result.cracked_password;
                                if (result.wordlist_used) {
                                    html += ' (usando: ' + result.wordlist_used + ')';
                                }
                                html += '</p>';
                                html += '</div>';
                            } else {
                                html += value + '</p>';
                            }
                        }
                    }
                    
                    // Mostrar fuente de datos
                    html += '<p class="source">Fuente: ' + result.data.source + '</p>';
                    html += '</div>';
                    html += '</div>';
                });
            }
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
                """)
    
    def load_databases(self):
        """Carga todas las bases de datos JSON del directorio de datos."""
        if not DATA_DIR.exists():
            print(f"Directorio {DATA_DIR} no encontrado. Creándolo...")
            DATA_DIR.mkdir(exist_ok=True)
            return
        
        
        json_files = list(DATA_DIR.glob("*.json"))
        if not json_files:
            print(f"No se encontraron archivos JSON en {DATA_DIR}")
            return
        
        print(f"Cargando {len(json_files)} bases de datos...")
        
        
        if self.discord_rpc:
            self.discord_rpc.update_presence(f"Cargando {len(json_files)} bases de datos")
        
        
        for json_file in tqdm(json_files, desc="Cargando bases de datos"):
            try:
                self.process_database(json_file)
            except Exception as e:
                print(f"Error al procesar {json_file.name}: {e}")
    
    def process_database(self, file_path: Path):
        """Procesa una base de datos JSON y extrae información de usuarios."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            source = file_path.name

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        username = None
                        for field in ['name', 'username', 'user', 'correo', 'email', 'login']:
                            if field in item:
                                username = item[field]
                                break
                        if username:
                            self.add_user_data(username, item, source)

            elif isinstance(data, dict):
                for username, user_data in data.items():
                    if isinstance(user_data, dict):
                        self.add_user_data(username, user_data, source)
                    else:
                        self.add_user_data(username, {"value": user_data}, source)

        except json.JSONDecodeError:
            print(f"Archivo {file_path.name} no es un JSON válido. Intentando recuperar datos parciales...")
            self.process_malformed_json(file_path)

    def search_user(self, username: str, check_premium: bool = True, crack_passwords: bool = True) -> Dict[str, Any]:
        """Busca un usuario en todas las bases de datos cargadas y verifica si es premium."""
        username = username.lower()
        results = []
        premium_info = None
        if self.discord_rpc:
            self.discord_rpc.update_presence(f"🔍 Buscando jugador: {username} 👀")
        if username in users_data:
            for data in users_data[username]:
                results.append({"data": data.copy()})
        if check_premium:
            try:
                if self.discord_rpc:
                    self.discord_rpc.update_presence(f"💎 Verificando cuenta premium: {username}")
                print(f"[*] Verificando si {username} es una cuenta premium...")
                premium_info = MinecraftPremiumChecker.check_premium_status(username)
                if not isinstance(premium_info, dict):
                    premium_info = {"is_premium": False, "error": "Formato de respuesta inválido"}
                elif "is_premium" not in premium_info:
                    premium_info["is_premium"] = False
                if premium_info["is_premium"]:
                    print("\033[92m[+]\033[0m ¡{username} ES UNA CUENTA PREMIUM!")
                    if premium_info.get("uuid"):
                        print(f"[+] UUID: {premium_info['uuid']}")
                else:
                    print(f"[-] {username} No es una cuenta premium.")
            except Exception as e:
                print(f"[!] Error al verificar estado premium: {e}")
                import traceback
                traceback.print_exc()
                premium_info = {"is_premium": False, "error": str(e)}
        else:
            print("\033[94m[*]\033[0m Verificación de cuenta premium desactivada")
        if crack_passwords:
            print(f"\033[94m[*]\033[0m Intentando romper hashes de contraseñas para {username}...")
            for result in results:
                password_hash = None
                for field in ['password', 'hash', 'password_hash', 'contrasena', 'passwd', 'clave', 'clave_hash', 'pass', 'pwd']:
                    if field in result['data']:
                        password_hash = result['data'][field]
                        break
                if password_hash:
                    if self.discord_rpc:
                        self.discord_rpc.update_presence(f"🧩 Rompiendo hashes de {username}... 🛠️")
                    print(f"[*] Intentando romper hash: {password_hash}")
                    cracked = HashCracker.crack_hash_with_all_wordlists(password_hash)
                    if cracked:
                        password, wordlist = cracked
                        print(f"\033[92m[✔] Hash roto! Contraseña: {password} (usando {wordlist})\033[0m")
                        result['cracked_password'] = password
                        result['wordlist_used'] = wordlist
        return {
            "results": results,
            "premium_info": premium_info
        }
def process_malformed_json(self, file_path: Path):
    """Intenta procesar un archivo JSON mal formado, línea por línea."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        source = file_path.name
        recovered_count = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    username = None
                    for field in ['name', 'username', 'user', 'correo', 'email', 'login']:
                        if field in item:
                            username = item[field]
                            break
                    if username:
                        self.add_user_data(username, item, source)
                        recovered_count += 1
            except:
                if any(key in line for key in ['"name"', '"username"', '"user"', '"correo"', '"email"', '"login"']):
                    parts = line.split('"')
                    for i, part in enumerate(parts):
                        if part in ['name', 'username', 'user', 'correo', 'email', 'login'] and i + 2 < len(parts):
                            username = parts[i + 2]
                            self.add_user_data(username, {"partial": "data_recovered"}, source)
                            recovered_count += 1
                            break

        if recovered_count > 0:
            print(f"Recuperados {recovered_count} registros de {file_path.name}")
        else:
            print(f"No se pudo recuperar ningún dato de {file_path.name}")

    except Exception as e:
        print(f"Error al procesar archivo malformado {file_path.name}: {e}")

    
    def search_user(self, username: str, check_premium: bool = True, crack_passwords: bool = True) -> Dict[str, Any]:
        """Busca un usuario en todas las bases de datos cargadas y verifica si es premium."""
        username = username.lower()
        results = []
        premium_info = None
        
        # Actualizar Discord RPC si está disponible
        if self.discord_rpc:
            self.discord_rpc.update_presence(f"🔍 Buscando jugador: {username} 👀")
        
        # Buscar en bases de datos
        if username in users_data:
            for data in users_data[username]:
                results.append({"data": data.copy()})
        
        # Verificar si es cuenta premium
        if check_premium:
            try:
                if self.discord_rpc:
                    self.discord_rpc.update_presence(f"💎 Verificando cuenta premium: {username}")
                
                print(f"\n[*] Verificando si {username} es una cuenta premium...")
                premium_info = MinecraftPremiumChecker.check_premium_status(username)
                
                # Asegurarse de que premium_info sea un diccionario válido y contenga la clave is_premium
                if not isinstance(premium_info, dict):
                    premium_info = {"is_premium": False, "error": "Formato de respuesta inválido"}
                elif "is_premium" not in premium_info:
                    premium_info["is_premium"] = False
                    
                # Imprimir resultado explícitamente para depuración
                if premium_info["is_premium"]:
                    print(f"[+] ¡{username} ES UNA CUENTA PREMIUM!")
                    if premium_info.get("uuid"):
                        print(f"[+] UUID: {premium_info['uuid']}")
                else:
                    print("\033[91m[-]\033[0m {username} no es una cuenta premium.")
            except Exception as e:
                print("\033[91m[!]\033[0m Error al verificar estado premium: {e}")
                import traceback
                traceback.print_exc()
                premium_info = {"is_premium": False, "error": str(e)}
        else:
            print("\033[94m[*]\033[0m Verificación de cuenta premium desactivada")
        
        # Intentar romper hashes de contraseñas
        if crack_passwords:
            print(f"\033[94m[*]\033[0m Intentando romper hashes de contraseñas para {username}...")
            
            for result in results:
                # Buscar campo de contraseña hash en los datos
                password_hash = None
                
                # Buscar en diferentes campos comunes para contraseñas
                for field in ['password', 'hash', 'password_hash', 'contrasena', 'passwd', 'clave', 'clave_hash', 'pass', 'pwd']:
                    if field in result['data']:
                        password_hash = result['data'][field]
                        break
                
                if password_hash:
                    # Actualizar Discord RPC si está disponible
                    if self.discord_rpc:
                        self.discord_rpc.update_presence(f"🧩 Rompiendo hashes de {username}... 🛠️")
                    
                    print(f"[*] Intentando romper hash: {password_hash}")
                    cracked = HashCracker.crack_hash_with_all_wordlists(password_hash)
                    
                    if cracked:
                        password, wordlist = cracked
                        print(f"\033[92m[✔] Hash roto! Contraseña: {password} (usando {wordlist})\033[0m")
                        result['cracked_password'] = password
                        result['wordlist_used'] = wordlist
        
        # Asegurarse de que siempre devolvemos el premium_info incluso si es None
        return {
            "results": results,
            "premium_info": premium_info
        }

os.chdir(WEB_DIR)

def start_server(user_finder):
    """Inicia el servidor web para la interfaz de usuario."""
    
    class FinderHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith('/search'):
                # Procesar solicitud de búsqueda
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                
                username = params.get('username', [''])[0]
                check_premium = params.get('check_premium', ['true'])[0].lower() == 'true'
                crack_passwords = params.get('crack_passwords', ['true'])[0].lower() == 'true'
                
                if username:
                    try:
                        # Obtener resultados
                        results = user_finder.search_user(username, check_premium, crack_passwords)
                        
                        # Asegurarse de que premium_info no sea None
                        if results.get('premium_info') is None:
                            results['premium_info'] = {"is_premium": False, "error": "No se pudo verificar el estado premium"}
                        
                        # Convertir a JSON y enviar respuesta
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        # Permitir solicitudes CORS
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps(results).encode())
                    except Exception as e:
                        # En caso de error, enviar respuesta de error
                        import traceback
                        error_details = traceback.format_exc()
                        print(f"ERROR durante la búsqueda: {e}")
                        print(error_details)
                        
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": str(e),
                            "details": error_details
                        }).encode())
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Nombre de usuario requerido"}).encode())
            elif self.path == '/':
                # Servir página principal
                self.path = '/index.html'
                return super().do_GET()
            else:
                # Para otros archivos estáticos
                return super().do_GET()
                
        def log_message(self, format, *args):
            # Activar los logs HTTP del servidor para depuración
            print(f"SERVIDOR WEB: {format % args}")
    
    port = 8080
    handler = FinderHandler
    
    print(f"\n\033[92m[+] Iniciando servidor web en el puerto {port}...\033[0m")
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"\033[92m[+] Interfaz web disponible en: http://localhost:{port}/\033[0m")
            
            # Abrir el navegador automáticamente
            webbrowser.open(f"http://localhost:{port}/")
            
            # Actualizar Discord RPC si está disponible
            if user_finder.discord_rpc:
                user_finder.discord_rpc.update_presence("Esperando búsquedas")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\033[93m[*] Servidor detenido\033[0m")
    except OSError as e:
        if e.errno == 98:  # Puerto en uso
            print(f"\033[91m[!] Error: El puerto {port} ya está en uso. Intenta cerrar otras aplicaciones o cambiar el puerto.\033[0m")
        else:
            print(f"\033[91m[!] Error al iniciar el servidor: {e}\033[0m")
def main():
    """Función principal del programa."""
    print("\n" + "=" * 70)
    print("\033[91m")
    print(r"""
  _____                                      _____                 _          
 / ____|                                    |  ___|               (_)         
| |  __  __ _ _ __   __ _      ______       | |__ _ __ ___  _ __   _ _ __ ___ 
| | |_ |/ _` | '_ \ / _` |    |______|      |  __| '_ ` _ \| '_ \ | | '__/ _ \
| |__| | (_| | | | | (_| |                  | |__| | | | | | |_) || | | |  __/
 \_____|\__,_|_| |_|\__, |                  \____/_| |_| |_| .__/ |_|_|  \___|
                     __/ |                                 |_|                
                    |___/                                    
    """)
    print("\033[0m" + "=" * 70)
    print("\033[93mGang Empire Finder Premium - La herramienta más potente para buscar información.\033[0m")
    print("\033[93m🔥 EL MEJOR FINDER DE MINECRAFT DEL MUNDO 🔥\033[0m")
    print("=" * 70 + "\n")
    
    # Inicializar Discord RPC si está disponible
    discord_rpc = None
    if DISCORD_RPC_AVAILABLE:
        discord_rpc = DiscordRPC()
    
    # Inicializar el buscador de usuarios
    user_finder = UserFinder(discord_rpc=discord_rpc)
    
    # Iniciar el servidor web
    start_server(user_finder)

if __name__ == "__main__":
    main()