#!/usr/bin/env python3
"""
Escanea la red local para encontrar routers/dispositivos
"""

import socket
import requests
import threading
from datetime import datetime
import os
import json

CONFIG_FILE = "router_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ip": "192.168.1.1"}

def get_local_subnet():
    """Detecta la subred local"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        # Asume /24 (clase C)
        parts = local_ip.split(".")
        subnet = ".".join(parts[:3])
        return subnet, local_ip
    except:
        return "192.168.1", "192.168.1.100"

def check_router(ip):
    """Verifica si una IP es un router con el endpoint conocido"""
    try:
        # Primero intenta el endpoint especifico
        url = f"http://{ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_=1"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': f'http://{ip}/html/stateOverview_inter.html',
        }
        resp = requests.get(url, headers=headers, timeout=2)
        if resp.status_code == 200:
            text = resp.text
            # Verifica si es un router FiberHome/Huawei
            if "sessionid" in text or "ModelName" in text or "GPON" in text:
                try:
                    data = resp.json()
                    return {
                        "ip": ip,
                        "modelo": data.get("ModelName", "N/A"),
                        "firmware": data.get("SoftwareVersion", "N/A"),
                        "wan": data.get("WANAccessType", "N/A")
                    }
                except:
                    return {"ip": ip, "info": "respondio pero no es JSON"}
        # Si no, intenta login page
        url2 = f"http://{ip}/"
        resp2 = requests.get(url2, timeout=2)
        if resp2.status_code == 200 and "login" in resp2.text.lower():
            return {"ip": ip, "info": "Tiene pagina de login (posible router)"}
    except:
        pass
    return None

def scan_subnet(subnet, start=1, end=255, max_workers=20):
    """Escanea la subred en paralelo"""
    results = []
    threads = []

    def worker(ip):
        result = check_router(ip)
        if result:
            results.append(result)
            print(f"  [ENCONTRADO] {result}")

    print(f"Escaneando {subnet}.{start}-{end}...")
    print()

    for i in range(start, end + 1):
        ip = f"{subnet}.{i}"
        t = threading.Thread(target=worker, args=(ip,), daemon=True)
        t.start()
        threads.append(t)

        if len(threads) >= max_workers:
            for t in threads:
                t.join()
            threads = []

    for t in threads:
        t.join()

    return results

def main():
    print("=" * 70)
    print("  ESCANEO DE RED - BUSCANDO ROUTERS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    subnet, local_ip = get_local_subnet()
    print(f"\n  Tu IP:        {local_ip}")
    print(f"  Subred:       {subnet}.x")
    print(f"  Objetivo:     Encontrar routers/dispositivos")
    print()

    # Escanear subred completa
    results = scan_subnet(subnet, 1, 254)

    print()
    print("=" * 70)
    print(f"  RESULTADOS: {len(results)} dispositivos encontrados")
    print("=" * 70)

    if results:
        print()
        for r in results:
            print(f"\n  IP: {r.get('ip')}")
            if "modelo" in r:
                print(f"    Modelo:   {r['modelo']}")
                print(f"    Firmware: {r['firmware']}")
                print(f"    WAN:      {r['wan']}")
            else:
                print(f"    Info:     {r.get('info', 'N/A')}")

        # Sugerir IP
        router_ips = [r["ip"] for r in results if "modelo" in r]
        if router_ips:
            print()
            print("=" * 70)
            print("  SUGERENCIA")
            print("=" * 70)
            print(f"  El router parece estar en: {router_ips[0]}")
            print(f"  Actualiza router_config.json con esta IP")

            # Preguntar si quiere actualizar
            print()
            resp = input(f"  Actualizar config a {router_ips[0]}? (s/n): ")
            if resp.lower() in ["s", "si", "yes", "y"]:
                config = load_config()
                config["ip"] = router_ips[0]
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"  [OK] Configuracion actualizada")
    else:
        print()
        print("  No se encontraron routers en la red.")
        print("  Posibles causas:")
        print("    - El router esta en otra subred")
        print("    - Hay firewall que bloquea las peticiones")
        print("    - Las credenciales o IP son diferentes")

    print()
    input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()