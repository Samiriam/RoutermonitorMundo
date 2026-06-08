#!/usr/bin/env python3
"""
Monitor para Router Huawei HG6145F - Mundo Chile
Consulta parametros: WiFi 5GHz, dispositivos, senal, trafico, CPU/memoria
Uso: python router_monitor.py
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json

ROUTER_IP = "192.168.1.1"
USERNAME = "user"
PASSWORD = "user1234"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def login():
    """Iniciar sesion en el router"""
    login_url = f"http://{ROUTER_IP}/login.cgi"
    data = {"username": USERNAME, "password": PASSWORD}
    resp = session.post(login_url, data=data, timeout=10)
    return resp.status_code == 200 or "success" in resp.text.lower()

def get_device_info():
    """Obtener informacion general del dispositivo"""
    url = f"http://{ROUTER_IP}/api/device-information"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def get_wifi_status():
    """Obtener estado de WiFi (2.4GHz y 5GHz)"""
    endpoints = [
        f"http://{ROUTER_IP}/api/wifi/0",
        f"http://{ROUTER_IP}/api/wifi/1",
        f"http://{ROUTER_IP}/api/wifi/2",
    ]
    results = []
    for ep in endpoints:
        try:
            resp = session.get(ep, timeout=10)
            if resp.status_code == 200:
                results.append(resp.text)
        except:
            pass
    return results if results else None

def get_connected_devices():
    """Obtener dispositivos conectados"""
    url = f"http://{ROUTER_IP}/api/devices"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def get_pon_status():
    """Obtener estado del enlace GPON (senal optica)"""
    url = f"http://{ROUTER_IP}/api/pon"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def get_traffic_stats():
    """Obtener estadisticas de trafico WAN/LAN"""
    url = f"http://{ROUTER_IP}/api/traffic"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def get_network_stats():
    """Obtener estadisticas de red (LAN, WAN)"""
    url = f"http://{ROUTER_IP}/api/network"
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def parse_simple_xml(xml_str):
    """Parsear XML simple sin namespaces"""
    if not xml_str:
        return {}
    try:
        root = ET.fromstring(xml_str)
        result = {}
        for elem in root.iter():
            if elem.text and elem.text.strip():
                result[elem.tag] = elem.text.strip()
        return result
    except:
        return {"raw": xml_str[:500]}

def print_separator():
    print("=" * 60)

def monitor():
    print_separator()
    print(f"MONITOR ROUTER HUAWEI HG6145F - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()

    if not login():
        print("[!] Error: No se pudo iniciar sesion en el router")
        print(f"    Verifica credenciales: {USERNAME}/{PASSWORD}")
        return

    print("[OK] Sesion iniciada correctamente")

    # Informacion del dispositivo
    info = get_device_info()
    if info:
        print("\n--- INFORMACION DEL DISPOSITIVO ---")
        data = parse_simple_xml(info)
        for k, v in data.items():
            print(f"  {k}: {v}")

    # Estado WiFi
    wifi = get_wifi_status()
    if wifi:
        print("\n--- ESTADO WiFi ---")
        for i, w in enumerate(wifi):
            print(f"  Banda {i}:")
            data = parse_simple_xml(w)
            for k, v in list(data.items())[:8]:
                print(f"    {k}: {v}")

    # Dispositivos conectados
    devs = get_connected_devices()
    if devs:
        print("\n--- DISPOSITIVOS CONECTADOS ---")
        data = parse_simple_xml(devs)
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  {k}:")
                for item in v:
                    print(f"    - {item}")
            else:
                print(f"  {k}: {v}")

    # Estado PON (senal optica)
    pon = get_pon_status()
    if pon:
        print("\n--- ESTADO GPON (Senal Optica) ---")
        data = parse_simple_xml(pon)
        for k, v in list(data.items())[:10]:
            print(f"  {k}: {v}")

    # Estadisticas de trafico
    traffic = get_traffic_stats()
    if traffic:
        print("\n--- TRAFICO WAN/LAN ---")
        data = parse_simple_xml(traffic)
        for k, v in list(data.items())[:10]:
            print(f"  {k}: {v}")

    print_separator()
    print("Monitoreo completado\n")

if __name__ == "__main__":
    monitor()