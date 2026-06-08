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

    # Try login with session
    print("\n2. Intentando login...")
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "loginpap": "1"
    }
    result = cgi_bin("login", login_data)
    print(f"   Response: {result[:300]}")
    return result

def get_device_info():
    """Obtiene informacion del dispositivo"""
    return cgi_bin("get_device_information")

def get_wifi_status():
    """Obtiene estado WiFi"""
    return cgi_bin("get_wifi_info")

def get_pon_status():
    """Obtiene estado GPON"""
    return cgi_bin("get_pon_status")

def get_devices():
    """Obtiene dispositivos conectados"""
    return cgi_bin("get_devices")

def get_wan_info():
    """Obtiene info WAN"""
    return cgi_bin("get_wan_info")

def get_network_info():
    """Obtiene info de red"""
    return cgi_bin("get_network_info")

def main():
    print("=" * 60)
    print(f"Huawei HG6145F Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Try login
    login_resp = login()

    # Try to get system info regardless
    print("\n3. Consultando informacion del sistema...")
    info = get_device_info()
    print(f"   Device Info: {info[:500]}")

    print("\n4. Consultando estado WiFi...")
    wifi = get_wifi_status()
    print(f"   WiFi Status: {wifi[:500]}")

    print("\n5. Consultando estado PON...")
    pon = get_pon_status()
    print(f"   PON Status: {pon[:500]}")

    print("\n6. Consultando dispositivos...")
    devs = get_devices()
    print(f"   Devices: {devs[:500]}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()