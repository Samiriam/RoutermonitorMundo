#!/usr/bin/env python3
"""
Diagnostico completo para problemas de conexion al router
"""

import requests
import json
import socket
import subprocess
import sys
import os
from datetime import datetime

CONFIG_FILE = "router_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ip": "192.168.1.1", "user": "user", "password": "user1234"}

def ping_test(host):
    """Hace ping al host"""
    try:
        param = "-n" if sys.platform.lower() == "win32" else "-c"
        result = subprocess.run(
            ["ping", param, "3", host],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def check_tcp_port(host, port, timeout=3):
    """Verifica si un puerto esta abierto"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_default_gateway():
    """Obtiene la puerta de enlace predeterminada"""
    try:
        if sys.platform.lower() == "win32":
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.split("\n"):
                if "Puerta de enlace" in line or "Default Gateway" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        gw = parts[1].strip()
                        if gw:
                            return gw
        return None
    except:
        return None

def test_http_endpoint(ip, endpoint, headers=None):
    """Prueba un endpoint HTTP"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': '*/*',
        }
    try:
        url = f"http://{ip}{endpoint}"
        resp = requests.get(url, headers=headers, timeout=5)
        return True, resp.status_code, resp.text[:200]
    except requests.exceptions.ConnectTimeout:
        return False, "TIMEOUT", ""
    except requests.exceptions.ConnectionError as e:
        return False, "CONNECTION_ERROR", str(e)[:200]
    except Exception as e:
        return False, "ERROR", str(e)[:200]

def scan_router():
    """Escanea IPs comunes del router"""
    common_ips = []
    base = "192.168"
    for b in [0, 1, 10, 100]:
        for c in [0, 1]:
            common_ips.append(f"{base}.{b}.{c}")
    for b in [1]:
        for c in range(1, 20):
            common_ips.append(f"{base}.{b}.{c}")

    return common_ips[:30]

def main():
    config = load_config()
    target_ip = config.get("ip", "192.168.1.1")
    user = config.get("user", "user")
    password = config.get("password", "user1234")

    print("=" * 70)
    print("  DIAGNOSTICO DE CONEXION AL ROUTER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Configuracion de red local
    print("\n[1] INFORMACION DE RED LOCAL")
    print("-" * 70)
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  Tu PC:       {hostname}")
        print(f"  Tu IP local: {local_ip}")
    except:
        print("  No se pudo obtener info local")

    gateway = get_default_gateway()
    if gateway:
        print(f"  Gateway:     {gateway}")
    else:
        print("  Gateway:     No detectado")

    # 2. Ping al router
    print(f"\n[2] PING A {target_ip}")
    print("-" * 70)
    success, output = ping_test(target_ip)
    if success:
        print(f"  [OK] {target_ip} responde a ping")
    else:
        print(f"  [ERROR] {target_ip} NO responde a ping")
        print(f"  Esto puede indicar que:")
        print(f"    - La IP es diferente en este lugar")
        print(f"    - El router bloquea ICMP (comun)")
        print(f"    - No tienes acceso al router desde esta red")

    # 3. Verificar puertos
    print(f"\n[3] PUERTOS DEL ROUTER ({target_ip})")
    print("-" * 70)
    ports = {
        80: "HTTP (Web normal)",
        443: "HTTPS (Web seguro)",
        8080: "HTTP alternativo",
        22: "SSH",
        23: "Telnet",
    }
    for port, desc in ports.items():
        if check_tcp_port(target_ip, port, timeout=2):
            print(f"  [ABIERTO] Puerto {port:5} - {desc}")
        else:
            print(f"  [CERRADO] Puerto {port:5} - {desc}")

    # 4. Probar endpoints HTTP
    print(f"\n[4] PROBANDO ENDPOINTS HTTP")
    print("-" * 70)
    endpoints = [
        ("/", "Pagina principal"),
        ("/cgi-bin/ajax?ajaxmethod=get_base_info&_=1", "API base_info"),
        ("/html/login_inter.html", "Pagina login"),
        ("/html/stateOverview_inter.html", "Pagina estado"),
    ]
    for endpoint, desc in endpoints:
        ok, status, text = test_http_endpoint(target_ip, endpoint)
        status_text = "OK" if ok else "FALLO"
        print(f"  [{status_text:5}] {desc}")
        if ok:
            print(f"          Status: {status}")
            print(f"          Muestra: {text[:100]}...")

    # 5. Probar con la sesion del navegador (headers correctos)
    print(f"\n[5] PROBANDO CON HEADERS DE NAVEGADOR")
    print("-" * 70)
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'Referer': f'http://{target_ip}/html/stateOverview_inter.html',
        'Accept': '*/*',
    }
    ok, status, text = test_http_endpoint(target_ip, "/cgi-bin/ajax?ajaxmethod=get_base_info&_=1", browser_headers)
    if ok and "sessionid" in text:
        print(f"  [OK] Router responde con datos del API")
        try:
            data = json.loads(text)
            print(f"  Modelo:     {data.get('ModelName', 'N/A')}")
            print(f"  Firmware:   {data.get('SoftwareVersion', 'N/A')}")
            print(f"  WAN:        {data.get('WANAccessType', 'N/A')}")
        except:
            pass
    else:
        print(f"  [FALLO] Status: {status}")
        print(f"  Texto: {text[:200]}")

    # 6. Busqueda de router en red local
    if gateway and gateway != target_ip:
        print(f"\n[6] COMPARACION DE GATEWAY")
        print("-" * 70)
        print(f"  IP objetivo: {target_ip}")
        print(f"  Gateway:     {gateway}")
        if gateway != target_ip:
            print(f"  [!] Las IPs son DIFERENTES")
            print(f"      El router real podria ser: {gateway}")
            print(f"      Prueba cambiar la IP en router_config.json")

    # 7. Sugerencias
    print(f"\n[7] DIAGNOSTICO Y SUGERENCIAS")
    print("=" * 70)
    print()
    print("  Si nada funciona, prueba lo siguiente:")
    print()
    print("  a) Abre el navegador y ve a http://{target_ip}")
    print("     Si no carga, la IP es incorrecta")
    print()
    print("  b) En el navegador, accede al router del colegio")
    print("     y busca la IP real en la barra de direcciones")
    print()
    print("  c) Verifica que estes en la misma red que el router")
    print("     Si el colegio usa VLANs, no podras acceder directamente")
    print()
    print("  d) Si el router del colegio es diferente, las")
    print("     credenciales user/user1234 podrian no funcionar")
    print()
    print("  e) Pregunta al administrador del colegio la IP")
    print("     y credenciales del router")
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
    print()
    input("Presiona ENTER para salir...")