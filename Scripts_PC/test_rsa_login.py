#!/usr/bin/env python3
"""
Login con RSA para router Mundo Chile firmware nuevo (RP3084+)
"""

import requests
import json
import base64
import os
import sys
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

CONFIG_FILE = "router_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ip": "192.168.1.1", "user": "user", "password": "user1234"}

def get_session_id(session, router_ip, headers):
    """Obtiene el sessionid del router"""
    url = f"http://{router_ip}/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid"
    resp = session.get(url, headers=headers, timeout=10)
    data = json.loads(resp.text)
    return data.get("sessionid")

def get_public_key(session, router_ip, headers):
    """Obtiene la clave publica RSA del router"""
    url = f"http://{router_ip}/fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt"
    resp = session.get(url, headers=headers, timeout=10)
    data = json.loads(resp.text)
    print(f"is_encrypt response: {data}")
    if data.get("enable") == 1:
        encrypted_key = data.get("data")
        # Decodificar la clave publica
        return base64.b64decode(encrypted_key)
    return None

def encrypt_password(password, public_key_data):
    """Encripta el password con la clave publica RSA"""
    try:
        # JSEncrypt usa PKCS#1
        # Agregar headers PEM si no los tiene
        if isinstance(public_key_data, bytes):
            public_key_data = public_key_data.decode('utf-8', errors='ignore')

        if not public_key_data.startswith("-----BEGIN"):
            # Es una clave PKCS#1 sin headers
            public_key_data = f"-----BEGIN RSA PUBLIC KEY-----\n{public_key_data}\n-----END RSA PUBLIC KEY-----"

        key = RSA.importKey(public_key_data)
        cipher = PKCS1_v1_5.new(key)
        encrypted = cipher.encrypt(password.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"Error con PKCS1: {e}")
        # Intentar con X.509
        try:
            if isinstance(public_key_data, bytes):
                public_key_data = public_key_data.decode('utf-8', errors='ignore')
            if not public_key_data.startswith("-----BEGIN"):
                public_key_data = f"-----BEGIN PUBLIC KEY-----\n{public_key_data}\n-----END PUBLIC KEY-----"
            key = RSA.importKey(public_key_data)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(password.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e2:
            print(f"Error con X.509: {e2}")
            return None

def do_login(session, router_ip, headers, username, password_encrypted, session_id):
    """Hace el login con password encriptado"""
    # Probar diferentes endpoints de login
    login_endpoints = [
        f"http://{router_ip}/fh_api/tmp/FHAPIS",
        f"http://{router_ip}/fh_api/FHAPIS",
        f"http://{router_ip}/fh_api/tmp/FHNCAPIS",
    ]

    for ep in login_endpoints:
        # Primero con ajaxmethod en query string
        url = f"{ep}?ajaxmethod=do_login&_={datetime.now().timestamp()}"
        data = {
            "yhm": username,
            "mm": password_encrypted,
            "sessionid": session_id
        }
        print(f"\nProbando: {url}")
        try:
            resp = session.post(url, data=data, headers=headers, timeout=10)
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {resp.text[:300]}")
            if resp.status_code == 200 and resp.text:
                try:
                    d = resp.json()
                    if "result" in d:
                        return d
                except:
                    pass
        except Exception as e:
            print(f"  Error: {e}")

    return None

def main():
    config = load_config()
    router_ip = config.get("ip", "192.168.1.1")
    username = config.get("user", "user")
    password = config.get("password", "user1234")

    print("=" * 70)
    print(f"  LOGIN CON RSA - Router {router_ip}")
    print(f"  Usuario: {username}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/main.html?5685',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    }

    # 1. Obtener session ID
    print("\n[1] Obteniendo session ID...")
    session_id = get_session_id(session, router_ip, headers)
    print(f"    Session ID: {session_id}")

    # 2. Obtener clave publica
    print("\n[2] Obteniendo clave publica RSA...")
    public_key = get_public_key(session, router_ip, headers)
    if public_key:
        print(f"    Clave publica obtenida: {len(public_key)} bytes")
        print(f"    Primeros 100 bytes: {public_key[:100]}")
    else:
        print("    [!] No se obtuvo clave publica")
        return

    # 3. Intentar diferentes formatos de clave
    print("\n[3] Encriptando password...")
    password_encrypted = None

    # La clave de JSEncrypt viene en formato PEM X.509
    # Agregar headers PEM si no los tiene
    key_str = public_key.decode('utf-8', errors='ignore')
    if not key_str.startswith("-----BEGIN"):
        key_str = f"-----BEGIN PUBLIC KEY-----\n{key_str}\n-----END PUBLIC KEY-----"

    password_encrypted = encrypt_password(password, key_str)
    if password_encrypted:
        print(f"    Password encriptado: {password_encrypted[:100]}...")
    else:
        print("    [!] No se pudo encriptar el password")
        return

    # 4. Hacer login
    print("\n[4] Haciendo login...")
    result = do_login(session, router_ip, headers, username, password_encrypted, session_id)

    if result:
        print(f"\n[5] Resultado del login: {result}")
        if result.get("result") == 0:
            print("    [OK] LOGIN EXITOSO!")
        else:
            print(f"    [!] Login fallo con codigo: {result.get('result')}")
    else:
        print("\n[!] No se obtuvo respuesta del login")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
    try:
        input("\nPresiona ENTER para salir...")
    except:
        pass