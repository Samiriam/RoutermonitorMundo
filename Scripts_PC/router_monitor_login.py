#!/usr/bin/env python3
"""
Monitor GPON con login completo - Router Mundo Chile (Huawei/FiberHome)
Soporta firmware antiguo (RP2934) y nuevo (RP3084+) con login AES
"""

import requests
import json
import os
import sys
import base64
import subprocess
from datetime import datetime
from Crypto.Cipher import AES

CONFIG_FILE = "router_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ip": "192.168.1.1", "user": "user", "password": "user1234"}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_new_firmware_data_via_browser(router_ip, username, password):
    helper_path = os.path.join(os.path.dirname(__file__), "router_web_client.js")
    result = subprocess.run(
        ["node", helper_path, router_ip, username, password],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )

    output = (result.stdout or "").strip()
    if not output:
        raise RuntimeError((result.stderr or "El helper web no devolvio salida").strip())

    parsed = json.loads(output.splitlines()[-1])
    if not parsed.get("success"):
        raise RuntimeError(parsed.get("error", "No se pudo autenticar por flujo web"))

    return parsed["data"]

def pkcs7_pad(data, block_size=16):
    """PKCS7 padding"""
    padding_len = block_size - (len(data) % block_size)
    if padding_len == 0:
        padding_len = block_size
    return data + chr(padding_len) * padding_len

def pkcs7_unpad(data):
    """Remove PKCS7 padding"""
    padding_len = data[-1]
    if isinstance(padding_len, int) and padding_len <= 16:
        return data[:-padding_len]
    return data

def int_aes_iv():
    """Genera IV para AES - chr(111) a chr(126)"""
    return ''.join(chr(i + 111) for i in range(16))

def init_aes_key(sessionid):
    """Genera clave AES desde sessionid - primeros 16 caracteres"""
    return sessionid[:16]

def aes_encrypt(data, key, iv):
    """Encripta con AES CBC + PKCS7"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(iv, str):
        iv = iv.encode('utf-8')

    # PKCS7 padding
    padded = pkcs7_pad(data.decode('utf-8')).encode('utf-8')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode('utf-8')

def aes_decrypt(data, key, iv):
    """Desencripta con AES CBC + PKCS7"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(iv, str):
        iv = iv.encode('utf-8')

    encrypted = base64.b64decode(data)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    return pkcs7_unpad(decrypted).decode('utf-8', errors='ignore')

def get_session_id(router_ip, session):
    """Obtiene session ID del router"""
    url = f"http://{router_ip}/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid&_={datetime.now().timestamp()}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/main.html?6802',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    }
    resp = session.get(url, headers=headers, timeout=10)
    data = json.loads(resp.text)
    return data.get("sessionid")

def login(router_ip, username, password, session):
    """Hace login en el router"""
    # Obtener sessionid
    session_id = get_session_id(router_ip, session)
    print(f"  Session ID: {session_id}")

    # Generar clave AES y IV
    g_fhKey = init_aes_key(session_id)
    g_fhIv = int_aes_iv()
    print(f"  AES Key: {g_fhKey}")
    print(f"  AES IV: {g_fhIv}")

    # Preparar datos de login (formato exacto del JS)
    login_data = {
        "yhm": username,
        "mm": password,
        "sessionid": session_id
    }
    # El JS usa JSON.stringify con formato especifico
    json_data = json.dumps(login_data, separators=(',', ':'))

    # Encriptar datos
    encrypted_data = aes_encrypt(json_data, g_fhKey, g_fhIv)
    print(f"  Datos encriptados: {encrypted_data[:50]}...")

    # Hacer POST con diferentes Content-Types
    url = f"http://{router_ip}/fh_api/FHAPIS?ajaxmethod=do_login&_={datetime.now().timestamp()}"

    # Intento 1: Content-Type application/json (como en el JS)
    headers1 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/main.html?6802',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json; charset=utf-8',
    }
    resp = session.post(url, data=encrypted_data, headers=headers1, timeout=10)
    print(f"  [JSON] Status: {resp.status_code}, Response: {resp.text[:200]}")

    if resp.status_code == 200 and '403' not in resp.text:
        try:
            result = json.loads(resp.text)
            if result.get("result") == 0:
                print(f"  [OK] Login exitoso!")
                return session_id, g_fhKey, g_fhIv
        except:
            pass

    # Intento 2: Como form data con campo 'data'
    headers2 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/main.html?6802',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    }
    resp = session.post(url, data={'data': encrypted_data}, headers=headers2, timeout=10)
    print(f"  [FORM] Status: {resp.status_code}, Response: {resp.text[:200]}")

    if resp.status_code == 200:
        try:
            result = json.loads(resp.text)
            if result.get("result") == 0:
                print(f"  [OK] Login exitoso!")
                return session_id, g_fhKey, g_fhIv
        except:
            pass

    print(f"  [ERROR] Ambos intentos fallaron")
    return None, None, None

def get_base_info(router_ip, session, session_id, g_fhKey, g_fhIv):
    """Obtiene informacion del router"""
    # Preparar datos
    request_data = {
        "sessionid": session_id
    }
    json_data = json.dumps(request_data, separators=(',', ':'))

    # Encriptar
    encrypted_data = aes_encrypt(json_data, g_fhKey, g_fhIv)

    # POST
    url = f"http://{router_ip}/fh_api/FHAPIS?ajaxmethod=get_base_info&_={datetime.now().timestamp()}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/main.html?6802',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json; charset=utf-8',
    }
    resp = session.post(url, data=encrypted_data, headers=headers, timeout=10)
    print(f"  Response: {resp.text[:500]}")

    try:
        data = json.loads(resp.text)
        return data
    except:
        return None

def format_bytes(b):
    if b is None:
        return "N/A"
    try:
        b = int(b)
        gb = b / (1024**3)
        if gb >= 1:
            return f"{gb:.2f} GB"
        mb = b / (1024**2)
        return f"{mb:.2f} MB"
    except:
        return str(b)

def format_uptime(s):
    try:
        s = int(s)
        dias = s // 86400
        horas = (s % 86400) // 3600
        minutos = (s % 3600) // 60
        if dias > 0:
            return f"{dias}d {horas}h {minutos}m"
        if horas > 0:
            return f"{horas}h {minutos}m"
        return f"{minutos}m"
    except:
        return str(s)

def main():
    config = load_config()
    router_ip = config.get("ip", "192.168.1.1")
    username = config.get("user", "user")
    password = config.get("password", "user1234")

    print("=" * 65)
    print("  MONITOR GPON - MUNDO CHILE (CON LOGIN AES)")
    print("=" * 65)
    print(f"  Router: {router_ip}")
    print(f"  Usuario: {username}")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    session = requests.Session()

    # Intentar primero con el endpoint simple (firmware antiguo)
    print("\n[1] Probando endpoint simple (firmware antiguo)...")
    simple_url = f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_={datetime.now().timestamp()}"
    simple_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
        'Accept': '*/*',
    }
    resp = session.get(simple_url, headers=simple_headers, timeout=10)
    if resp.status_code == 200:
        try:
            data = json.loads(resp.text)
            if "sessionid" in data and "ponBytesSent" in data:
                print(f"  [OK] Router VIEJO detectado - datos directos")
                # Mostrar datos directamente
                uptime = int(data.get('uptime', 0))
                pon_sent = int(data.get('ponBytesSent', 0))
                pon_recv = int(data.get('ponBytesReceived', 0))

                print(f"\n  [UPTIME] Activo: {format_uptime(uptime)}")
                print(f"  [TRAFICO GPON]")
                print(f"    Enviado:   {format_bytes(pon_sent)}")
                print(f"    Recibido:  {format_bytes(pon_recv)}")
                print(f"    Total:     {format_bytes(pon_sent + pon_recv)}")
                print(f"  [SISTEMA]")
                print(f"    CPU: {data.get('cpu_usage', 'N/A')}%")
                print(f"    Modelo: {data.get('ModelName', 'N/A')}")
                print(f"    Firmware: {data.get('SoftwareVersion', 'N/A')}")
                return
        except:
            pass

    # Si no funciona el endpoint simple, intentar con login AES
    print(f"  [INFO] Endpoint simple no funciona, usando flujo web real del firmware nuevo...")

    try:
        data = get_new_firmware_data_via_browser(router_ip, username, password)
    except Exception as exc:
        print(f"\n[!] No se pudo completar el login web: {exc}")
        return

    print("\n[2] Datos obtenidos del firmware nuevo")
    print(f"  Modelo: {data.get('ModelName', 'N/A')}")
    print(f"  Firmware: {data.get('SoftwareVersion', 'N/A')}")
    print(f"  Uptime: {format_uptime(data.get('uptime', 0))}")
    print(f"  CPU: {data.get('cpu_usage', 'N/A')}%")
    print(f"  RAM: {format_bytes(int(data.get('mem_free', 0)))} free / {format_bytes(int(data.get('mem_total', 0)))} total")
    print(f"  WAN/PON: {data.get('WANAccessType', 'N/A')}")
    if data.get('txpower') or data.get('rxpower'):
        print(f"  Optica TX/RX: {data.get('txpower', 'N/A')} dBm / {data.get('rxpower', 'N/A')} dBm")
        print(f"  Optica Temp/Volt/Bias: {data.get('transceivertemperature', 'N/A')}C / {data.get('supplyvottage', 'N/A')}V / {data.get('biascurrent', 'N/A')}mA")

    # WiFi 5GHz
    if data.get('wifi5_bytes_sent') or data.get('wifi5_bytes_received'):
        print(f"  WiFi 5G ({data.get('wifi5_ssid_1','')}): enviado={format_bytes(data.get('wifi5_bytes_sent'))}, recibido={format_bytes(data.get('wifi5_bytes_received'))}, canal={data.get('wifi5_channel','')}")

    # WiFi 2.4GHz
    if data.get('wifi24_bytes_sent') or data.get('wifi24_bytes_received'):
        print(f"  WiFi 2.4G ({data.get('wifi24_ssid_1','')}): enviado={format_bytes(data.get('wifi24_bytes_sent'))}, recibido={format_bytes(data.get('wifi24_bytes_received'))}, canal={data.get('wifi24_channel','')}")

    # LAN ports
    has_lan = any(data.get(f'lan{i}_status', '') for i in range(1, 10))
    if has_lan:
        for i in range(1, 10):
            status = data.get(f'lan{i}_status', '')
            if not status:
                continue
            sent = int(data.get(f'lan{i}_bytes_sent', 0) or 0)
            recv = int(data.get(f'lan{i}_bytes_received', 0) or 0)
            print(f"  LAN Port {i}: {status}, enviado={format_bytes(sent)}, recibido={format_bytes(recv)}")

    if data.get('NOTA'):
        print(f"  Nota: {data['NOTA']}")

    print("\n" + "=" * 65)
    print("  FIN")
    print("=" * 65)

if __name__ == "__main__":
    main()
    try:
        input("\nPresiona ENTER para salir...")
    except:
        pass
