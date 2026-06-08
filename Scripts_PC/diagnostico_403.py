#!/usr/bin/env python3
"""
Diagnostico especifico para error 403 Forbidden
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

def test_full_flow(router_ip, user, password):
    """Prueba el flujo completo de conexion"""
    session = requests.Session()
    print(f"\nProbando conexion a {router_ip} con usuario '{user}'...")
    print("=" * 70)

    # 1. Acceso sin credenciales
    print("\n[1] Acceso sin credenciales:")
    try:
        resp = session.get(f"http://{router_ip}/", timeout=5)
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 403:
            print(f"    [403] Acceso denegado - IP bloqueada o router restringido")
            return "ip_blocked"
    except Exception as e:
        print(f"    Error: {e}")
        return "no_connection"

    # 2. Intentar endpoint del API
    print("\n[2] Probando endpoint API (get_base_info):")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
        'Accept': '*/*',
    }
    try:
        url = f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_={datetime.now().timestamp()}"
        resp = session.get(url, headers=headers, timeout=5)
        print(f"    Status: {resp.status_code}")
        print(f"    Respuesta: {resp.text[:300]}")

        if resp.status_code == 403:
            print(f"\n    [403 FORBIDDEN] - El router rechaza el acceso")
            print(f"    Posibles causas:")
            print(f"      a) Tu IP esta bloqueada en el firewall del router")
            print(f"      b) Las credenciales no son validas para este router")
            print(f"      c) El router tiene restricciones de acceso por horario")
            print(f"      d) El colegio configuro el router para no responder")
            return "403"
        elif resp.status_code == 200:
            try:
                data = resp.json()
                if "sessionid" in data:
                    print(f"    [OK] Conexion exitosa!")
                    print(f"    Modelo: {data.get('ModelName', 'N/A')}")
                    return "success"
            except:
                pass
    except Exception as e:
        print(f"    Error: {e}")
        return "error"

    # 3. Probar login
    print("\n[3] Probando login:")
    try:
        login_url = f"http://{router_ip}/"
        login_data = {
            "username": user,
            "password": password
        }
        resp = session.post(login_url, data=login_data, timeout=5)
        print(f"    Status: {resp.status_code}")
        if "403" in resp.text or "Forbidden" in resp.text:
            print(f"    [403] Login rejectedo")
    except Exception as e:
        print(f"    Error: {e}")

    return "unknown"

def main():
    config = load_config()
    router_ip = config.get("ip", "192.168.1.1")
    user = config.get("user", "user")
    password = config.get("password", "user1234")

    print("=" * 70)
    print("  DIAGNOSTICO ERROR 403 FORBIDDEN")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\n  IP objetivo: {router_ip}")
    print(f"  Usuario:     {user}")
    print(f"  Password:    {'*' * len(password)}")

    result = test_full_flow(router_ip, user, password)

    print("\n" + "=" * 70)
    print("  RECOMENDACIONES")
    print("=" * 70)

    if result == "403":
        print("""
El router del COLEGIO esta bloqueando tu acceso. Esto es comun en
entornos institucionales. Posibles soluciones:

1. HABLAR CON EL ADMINISTRADOR DE RED DEL COLEGIO
   - Pedir acceso temporal al panel del router
   - Solicitar las credenciales correctas (pueden ser diferentes)
   - Pedir que abran el acceso desde tu IP

2. VERIFICAR LA IP DEL ROUTER
   - Abre el navegador y ve a http://192.168.1.1
   - Si da 403, prueba otras IPs comunes:
     * 192.168.0.1
     * 10.0.0.1
     * 192.168.100.1
     * gateway de tu red (ejecuta 'ipconfig' en cmd)

3. USAR CREDENCIALES DIFERENTES
   - El colegio puede tener otras claves distintas a user/user1234
   - Edita router_config.json con las correctas

4. VERIFICAR QUE ESTES EN LA RED DEL COLEGIO
   - Si el colegio usa captive portal, primero autenticate
   - Si hay VLANs, no podras acceder al router desde otra VLAN

5. INTENTAR DESDE LA APP MOVIL DEL COLEGIO
   - Algunos colegios tienen una app para gestion de red

IMPORTANTE: Si el colegio no quiere que accedas al router,
respeta esa decision. Es su equipo y su red.
""")
    elif result == "ip_blocked":
        print("""
Tu IP esta siendo bloqueada por el firewall del router.

Soluciones:
- Hablar con el administrador del colegio
- Verificar que estes en la red correcta
- Esperar unos minutos (algunos bloqueos son temporales)
""")
    elif result == "no_connection":
        print("""
No se puede conectar al router.

Verifica:
- Que estes conectado a la red WiFi/Ethernet del colegio
- La IP correcta del router (puede no ser 192.168.1.1)
- Que el router este encendido
""")
    elif result == "success":
        print("""
Conexion exitosa! Todo funciona correctamente.

El error 403 que viste antes pudo ser temporal.
""")
    else:
        print("""
No se pudo determinar la causa exacta.

Recomendaciones:
- Ejecuta la opcion 6 (Escanear red) del menu
- Verifica que estes en la red correcta
- Habla con el administrador del colegio
""")

    print("=" * 70)
    print()
    input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()