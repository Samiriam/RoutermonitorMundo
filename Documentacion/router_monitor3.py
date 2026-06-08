#!/usr/bin/env python3
"""
Monitor para Router Huawei HG6145F - Mundo Chile
Usa el CGI-bin AJAX endpoint del firmware
"""

import requests
import json
from datetime import datetime

ROUTER_IP = "192.168.1.1"
USERNAME = "user"
PASSWORD = "user1234"

session = requests.Session()

def cgi_bin(method, data=None):
    """Hace petition al endpoint CGI-bin del router"""
    url = f"http://{ROUTER_IP}/cgi-bin/ajax"
    params = {"ajaxmethod": method}
    if data:
        data["ajaxmethod"] = method
        data["_"] = str(datetime.now().timestamp())
    else:
        params["_"] = str(datetime.now().timestamp())
    try:
        resp = session.post(url, data=data, params=params, timeout=10)
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def get_sessionid():
    """Obtiene session ID primero"""
    url = f"http://{ROUTER_IP}/cgi-bin/ajax?ajaxmethod=get_refresh_sessionid&_={datetime.now().timestamp()}"
    try:
        resp = session.get(url, timeout=10)
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def login():
    """Intenta iniciar sesion"""
    # First get session
    print("1. Obteniendo session ID...")
    sess_resp = get_sessionid()
    print(f"   Response: {sess_resp[:200]}")
    session_id = None
    try:
        data = json.loads(sess_resp)
        session_id = data.get("sessionid")
    except:
        pass

    # Try login with session
    print("\n2. Intentando login con session ID...")
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "sessionid": session_id
    }
    result = cgi_bin("login", login_data)
    print(f"   Response: {result[:300]}")
    return session_id

def query(method, session_id=None):
    """Hace una query al router"""
    url = f"http://{ROUTER_IP}/cgi-bin/ajax"
    data = {}
    if session_id:
        data["sessionid"] = session_id
    data["ajaxmethod"] = method
    data["_"] = str(datetime.now().timestamp())

    try:
        resp = session.post(url, data=data, timeout=10)
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 60)
    print(f"Huawei HG6145F Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Login and get session
    session_id = login()

    if not session_id:
        print("[!] No se pudo obtener session ID")
        return

    print(f"\n3. Session ID: {session_id}")

    # Queries con session
    queries = [
        ("get_device_information", "Device Info"),
        ("get_wifi_info", "WiFi Status"),
        ("get_pon_status", "PON Status"),
        ("get_devices", "Connected Devices"),
        ("get_wan_info", "WAN Info"),
        ("get_network_info", "Network Info"),
    ]

    for method, name in queries:
        print(f"\n4. Consultando {name}...")
        result = query(method, session_id)
        print(f"   Response: {result[:400]}")
        print()

    print("=" * 60)

if __name__ == "__main__":
    main()