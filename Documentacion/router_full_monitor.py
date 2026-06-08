#!/usr/bin/env python3
"""
Monitor completo para Huawei HG6145F - Mundo Chile
Usa el endpoint correcto con headers de navegador
"""

import requests
import json
from datetime import datetime

ROUTER_IP = "192.168.1.1"

session = requests.Session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'Referer': 'http://192.168.1.1/html/stateOverview_inter.html',
    'Accept': '*/*',
}

def get_data(method):
    """Obtiene datos del endpoint"""
    url = f"http://{ROUTER_IP}/cgi-bin/ajax?ajaxmethod={method}&_={datetime.now().timestamp()}"
    try:
        resp = session.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return json.loads(resp.text)
    except:
        pass
    return None

def print_section(title, data):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)
    if data:
        for key, value in data.items():
            print(f"  {key}: {value}")
    else:
        print("  No data received")

def main():
    print("=" * 60)
    print("MONITOR HUAWEI HG6145F - MUNDO CHILE")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Info basica
    data = get_data("get_base_info")
    print_section("INFORMACION GENERAL", data)

    # 2. WiFi info
    data = get_data("get_wifi_info")
    print_section("ESTADO WiFi", data)

    # 3. PON status (senal optica)
    data = get_data("get_pon_status")
    print_section("Senal GPON", data)

    # 4. Dispositivos conectados
    data = get_data("get_devices")
    print_section("DISPOSITIVOS CONECTADOS", data)

    # 5. Info de red
    data = get_data("get_network_info")
    print_section("INFORMACION DE RED", data)

    # 6. WAN info
    data = get_data("get_wan_info")
    print_section("INFORMACION WAN", data)

    # 7. Traffic stats
    data = get_data("get_traffic_stats")
    print_section("ESTADISTICAS DE TRAFICO", data)

    print("\n" + "=" * 60)
    print("MONITOREO COMPLETO")
    print("=" * 60)

    # Guardar en archivo
    with open(f"router_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as f:
        f.write(f"Monitor Huawei HG6145F - {datetime.now()}\n")
        f.write(f"Session ID: {get_data('get_base_info', headers=headers).get('sessionid', 'N/A') if get_data('get_base_info') else 'N/A'}\n")

if __name__ == "__main__":
    main()