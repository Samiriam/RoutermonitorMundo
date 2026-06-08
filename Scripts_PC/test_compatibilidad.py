#!/usr/bin/env python3
"""
Test que cierra sesion activa antes de intentar nuevas conexiones
Compatible con ambos routers (casa FW viejo y colegio FW nuevo)
"""

import requests
import json
import os
import sys
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

def test_old_firmware(router_ip):
    """Prueba router con firmware viejo (casa - HG6145F)"""
    print("=" * 70)
    print("  TEST ROUTER VIEJO (CASA - HG6145F - FW RP2934)")
    print("=" * 70)

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
        'Accept': '*/*',
    }

    try:
        url = f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_={datetime.now().timestamp()}"
        resp = session.get(url, headers=headers, timeout=10)
        print(f"\n[1] GET /cgi-bin/ajax?ajaxmethod=get_base_info")
        print(f"    Status: {resp.status_code}")

        if resp.status_code == 200:
            data = json.loads(resp.text)
            if "sessionid" in data:
                print(f"    [OK] Router VIEJO responde")
                print(f"    Modelo:    {data.get('ModelName', 'N/A')}")
                print(f"    Firmware:  {data.get('SoftwareVersion', 'N/A')}")
                print(f"    WAN:       {data.get('WANAccessType', 'N/A')}")
                print(f"    Uptime:    {data.get('uptime', 'N/A')} segundos")
                print(f"    CPU:       {data.get('cpu_usage', 'N/A')}%")
                sent = int(data.get('ponBytesSent', 0))
                recv = int(data.get('ponBytesReceived', 0))
                print(f"    GPON Sent: {sent:,} bytes")
                print(f"    GPON Recv: {recv:,} bytes")
                return True, data
        else:
            print(f"    [FALLO] {resp.status_code}")
            return False, None
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False, None

def test_new_firmware(router_ip):
    """Prueba router con firmware nuevo (colegio - HG5853SF)"""
    print("\n" + "=" * 70)
    print("  TEST ROUTER NUEVO (COLEGIO - HG5853SF - FW RP3084)")
    print("=" * 70)

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'Referer': f'http://{router_ip}/main.html?6802',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
    }

    # 1. Heartbeat (publico)
    print("\n[1] GET /fh_api/tmp/heartbeat (publico)")
    try:
        url = f"http://{router_ip}/fh_api/tmp/heartbeat"
        resp = session.get(url, headers=headers, timeout=10)
        print(f"    Status: {resp.status_code}")
        print(f"    Response: {resp.text[:200]}")
    except Exception as e:
        print(f"    [ERROR] {e}")

    # 2. Intentar logout (puede que cierre la sesion del navegador)
    print("\n[2] Intentando cerrar sesion activa (DO_WEB_LOGOUT)...")
    logout_endpoints = [
        f"http://{router_ip}/fh_api/DO_WEB_LOGOUT",
        f"http://{router_ip}/fh_api/do_web_logout",
        f"http://{router_ip}/fh_api/tmp/logout",
        f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=do_logout",
    ]
    for ep in logout_endpoints:
        try:
            resp = session.get(ep, headers=headers, timeout=5)
            if resp.status_code == 200:
                print(f"    {ep}: {resp.status_code} - {resp.text[:100]}")
        except:
            pass

    # 3. Intentar login con diferentes metodos
    print("\n[3] Probando login sin encriptacion...")
    login_endpoints = [
        f"http://{router_ip}/fh_api/DO_WEB_LOGIN",
        f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=do_login",
    ]
    for ep in login_endpoints:
        try:
            # Probar GET
            resp = session.get(ep, headers=headers, timeout=5)
            print(f"    GET  {ep}: {resp.status_code} - {resp.text[:100]}")
            # Probar POST
            resp = session.post(ep, data={"yhm": "user", "mm": "user1234"}, headers=headers, timeout=5)
            print(f"    POST {ep}: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"    {ep}: ERROR - {e}")

    return False, None

def detect_router_type(router_ip):
    """Detecta que tipo de router responde"""
    session = requests.Session()

    # Probar endpoint del router nuevo PRIMERO
    headers_new = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': f'http://{router_ip}/main.html?6802',
        'X-Requested-With': 'XMLHttpRequest',
    }
    try:
        resp = session.get(
            f"http://{router_ip}/fh_api/tmp/heartbeat",
            headers=headers_new, timeout=5
        )
        if resp.status_code == 200:
            return "NEW", "FW_RP3084_o_superior"
    except:
        pass

    # Probar endpoint del router viejo
    headers_old = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
    }
    try:
        resp = session.get(
            f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_=1",
            headers=headers_old, timeout=5
        )
        if resp.status_code == 200 and "sessionid" in resp.text:
            return "OLD", "HG6145F_FW_RP2934"
    except:
        pass

    return "UNKNOWN", "desconocido"

def main():
    config = load_config()
    router_ip = config.get("ip", "192.168.1.1")
    user = config.get("user", "user")
    password = config.get("password", "user1234")

    print("=" * 70)
    print(f"  TEST COMPLETO DE COMPATIBILIDAD")
    print(f"  Router: {router_ip}")
    print(f"  Usuario: {user}")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Detectar tipo de router
    print("\n[DETECCION] Identificando router...")
    router_type, model = detect_router_type(router_ip)
    print(f"  Tipo detectado: {router_type}")
    print(f"  Modelo:         {model}")

    # Probar segun el tipo
    if router_type == "OLD":
        ok, data = test_old_firmware(router_ip)
        if ok:
            print("\n[RESULTADO] Router VIEJO funciona correctamente con el script")
    elif router_type == "NEW":
        ok, data = test_new_firmware(router_ip)
        if not ok:
            print("\n[RESULTADO] Router NUEVO detectado pero requiere login con AES")
            print("            Pendiente: capturar trafico del navegador para implementar login")
    else:
        print("\n[!] No se pudo detectar el tipo de router")

    print("\n" + "=" * 70)
    print("  FIN DEL TEST")
    print("=" * 70)

if __name__ == "__main__":
    main()