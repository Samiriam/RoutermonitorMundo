#!/usr/bin/env python3
"""
Monitor para Router Huawei HG6145F - Mundo Chile
Soporta login con password encriptado AES
Uso: python router_monitor.py
"""

import requests
import json
import base64
from datetime import datetime
from Crypto.Cipher import AES

ROUTER_IP = "192.168.1.1"
USERNAME = "user"
PASSWORD = "user1234"

session = requests.Session()

def int_aes_iv():
    """Genera el IV para AES (chars 111-126, 16 bytes)"""
    return ''.join(chr(i + 111) for i in range(16))

def aes_encrypt(data, key, iv):
    """Encripta data con AES CBC"""
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    # PKCS7 padding
    block_size = 16
    padding = block_size - (len(data) % block_size)
    data += chr(padding) * padding
    encrypted = cipher.encrypt(data.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

def fhencrypt(password):
    """Encripta password como lo hace el router"""
    iv = int_aes_iv()
    key = iv
    return aes_encrypt(password, key, iv).upper()

def cgi_get(method):
    """GET request al CGI-bin"""
    url = f"http://{ROUTER_IP}/cgi-bin/ajax"
    params = {"ajaxmethod": method, "_": datetime.now().timestamp()}
    try:
        resp = session.get(url, params=params, timeout=10)
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def cgi_post(method, data=None):
    """POST request al CGI-bin"""
    url = f"http://{ROUTER_IP}/cgi-bin/ajax"
    params = {"ajaxmethod": method}
    if data is None:
        data = {}
    data["ajaxmethod"] = method
    data["_"] = datetime.now().timestamp()
    try:
        resp = session.post(url, data=data, params=params, timeout=10)
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def login():
    """Inicia sesion en el router"""
    print("[1] Obteniendo factory_mode...")
    factory = cgi_get("get_factory_mode")
    print(f"    Response: {factory[:200]}")

    session_id = None
    try:
        data = json.loads(factory)
        session_id = data.get("sessionid", "")
    except:
        pass

    if not session_id:
        print("[!] No se pudo obtener session ID")
        return None

    print(f"\n[2] Session ID: {session_id}")

    print("[3] Obteniendo operator_test...")
    operator = cgi_get("get_operator_test")
    print(f"    Response: {operator[:200]}")

    try:
        data = json.loads(operator)
        if data.get("sessionid"):
            session_id = data["sessionid"]
            print(f"    Nueva session: {session_id}")
    except:
        pass

    print(f"\n[4] Enviando login con password encriptado...")
    encrypted_pass = fhencrypt(PASSWORD)
    login_data = {
        "username": USERNAME,
        "loginpd": encrypted_pass,
        "port": "0",
        "sessionid": session_id
    }
    result = cgi_post("do_login", login_data)
    print(f"    Response: {result[:300]}")

    try:
        data = json.loads(result)
        if data.get("login_result") == 0:
            print("\n[OK] Login exitoso!")
            return session_id
        else:
            print(f"\n[!] Login failed: result={data.get('login_result')}")
    except:
        pass

    return None

def query(method, session_id):
    """Query con session ID"""
    data = {"sessionid": session_id}
    return cgi_post(method, data)

def pretty_json(text):
    """Intenta formatear JSON"""
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except:
        return text

def main():
    print("=" * 60)
    print(f"Huawei HG6145F Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    session_id = login()

    if not session_id:
        print("\n[!] No se pudo iniciar sesion")
        print("    Posibles causas:")
        print("    - Credenciales incorrectas (user/user1234)")
        print("    - Router no responde correctamente")
        print("    - Captcha requerido (no soportado)")
        return

    print("\n" + "=" * 60)
    print("CONSULTANDO PARAMETROS DEL ROUTER")
    print("=" * 60)

    queries = [
        ("get_device_information", "Informacion del Dispositivo"),
        ("get_wifi_info", "Estado WiFi (2.4GHz/5GHz)"),
        ("get_pon_status", "Estado GPON (Senal Optica)"),
        ("get_devices", "Dispositivos Conectados"),
        ("get_wan_info", "Informacion WAN"),
        ("get_network_info", "Estado de Red"),
        ("get_system_status", "Estado del Sistema"),
    ]

    for method, name in queries:
        print(f"\n--- {name} ---")
        result = query(method, session_id)
        print(pretty_json(result)[:500])
        print()

if __name__ == "__main__":
    main()