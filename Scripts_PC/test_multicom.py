#!/usr/bin/env python3
"""
Prueba directa con el router HG5853SF de Multicom
"""

import requests
import json
from datetime import datetime

ROUTER_IP = "192.168.1.1"
USER = "user"
PASSWORD = "user1234"

session = requests.Session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'Referer': f'http://{ROUTER_IP}/html/stateOverview_inter.html',
    'Accept': '*/*',
}

print("=" * 70)
print("  PRUEBA ROUTER MULTICOM HG5853SF")
print("  (debe ejecutarse desde el colegio)")
print("=" * 70)

# Probar endpoint directamente
print("\n[1] Probando endpoint get_base_info...")
url = f"http://{ROUTER_IP}/cgi-bin/ajax?ajaxmethod=get_base_info&_={datetime.now().timestamp()}"
try:
    resp = session.get(url, headers=headers, timeout=10)
    print(f"    Status: {resp.status_code}")
    print(f"    Headers: {dict(resp.headers)}")
    print(f"    Respuesta:")
    print(f"    {resp.text[:1500]}")
except Exception as e:
    print(f"    Error: {e}")

# Probar otras URLs
print("\n[2] Probando otras URLs...")
urls_to_test = [
    ("/", "Pagina principal"),
    ("/html/login_inter.html", "Login"),
    ("/html/main.html", "Main"),
    ("/html/stateOverview_inter.html", "Estado"),
]
for path, desc in urls_to_test:
    url = f"http://{ROUTER_IP}{path}"
    try:
        resp = session.get(url, headers=headers, timeout=5)
        print(f"\n    {desc} ({path})")
        print(f"      Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"      OK - Length: {len(resp.text)}")
        elif resp.status_code == 403:
            print(f"      403 FORBIDDEN")
        else:
            print(f"      Texto: {resp.text[:200]}")
    except Exception as e:
        print(f"      Error: {e}")

print("\n" + "=" * 70)