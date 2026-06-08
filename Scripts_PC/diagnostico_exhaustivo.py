#!/usr/bin/env python3
"""
Prueba exhaustiva del router - HTTPS, otros puertos, diferentes paths
"""

import requests
import json
import os
import sys
from datetime import datetime
import urllib3

# Desactivar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG_FILE = "router_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ip": "192.168.1.1", "user": "user", "password": "user1234"}

def test_endpoint(url, headers=None, use_ssl=False, label=""):
    """Prueba un endpoint"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        }
    try:
        if use_ssl:
            resp = requests.get(url, headers=headers, timeout=5, verify=False)
        else:
            resp = requests.get(url, headers=headers, timeout=5)
        return resp.status_code, resp.text[:300]
    except requests.exceptions.SSLError as e:
        return "SSL_ERROR", str(e)[:200]
    except requests.exceptions.ConnectTimeout:
        return "TIMEOUT", ""
    except requests.exceptions.ConnectionError as e:
        return "CONN_ERROR", str(e)[:200]
    except Exception as e:
        return "ERROR", str(e)[:200]

def main():
    config = load_config()
    router_ip = config.get("ip", "192.168.1.1")

    print("=" * 70)
    print("  PRUEBA EXHAUSTIVA DEL ROUTER")
    print(f"  Router: {router_ip}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Variantes a probar
    variants = [
        # (protocolo, puerto, path, descripcion)
        ("http", 80, "/", "HTTP Puerto 80 - raiz"),
        ("http", 80, "/html/login_inter.html", "HTTP 80 - login"),
        ("http", 80, "/cgi-bin/ajax?ajaxmethod=get_base_info&_=1", "HTTP 80 - API"),
        ("http", 80, "/cgi-bin/ajax?ajaxmethod=get_base_info&_=1", "HTTP 80 - API con Referer"),
        ("https", 443, "/", "HTTPS Puerto 443 - raiz"),
        ("https", 443, "/html/login_inter.html", "HTTPS 443 - login"),
        ("https", 443, "/cgi-bin/ajax?ajaxmethod=get_base_info&_=1", "HTTPS 443 - API"),
        ("http", 8080, "/", "HTTP Puerto 8080"),
        ("http", 8443, "/", "HTTP Puerto 8443"),
        ("http", 80, "/index.html", "HTTP 80 - index.html"),
    ]

    print("\n[1] PROBANDO DIFERENTES COMBINACIONES")
    print("=" * 70)

    for proto, port, path, desc in variants:
        url = f"{proto}://{router_ip}:{port}{path}"
        use_ssl = proto == "https"

        # Agregar Referer para los endpoints del API
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        }
        if "cgi-bin" in path:
            headers['Referer'] = f'http://{router_ip}/html/stateOverview_inter.html'

        status, text = test_endpoint(url, headers, use_ssl)
        print(f"\n  {desc}")
        print(f"    URL: {url}")
        print(f"    Status: {status}")
        if status == 200:
            # Ver si tiene datos
            if "sessionid" in text or "ModelName" in text:
                print(f"    [OK] Respuesta con datos del router!")
                try:
                    data = json.loads(text)
                    print(f"    Modelo: {data.get('ModelName', 'N/A')}")
                    print(f"    Firmware: {data.get('SoftwareVersion', 'N/A')}")
                except:
                    pass
            elif "<html" in text.lower() or "<!doctype" in text.lower():
                print(f"    [OK] Pagina HTML recibida")
                if "login" in text.lower():
                    print(f"    [INFO] Es la pagina de login")
            else:
                print(f"    Muestra: {text[:100]}")
        elif status == 403:
            print(f"    [403 FORBIDDEN]")
        elif status == 404:
            print(f"    [404 NOT FOUND]")
        elif status == 302:
            print(f"    [302 REDIRECT] Redireccion")
        elif status == "SSL_ERROR":
            print(f"    [SSL Error] {text[:100]}")
        elif status == "CONN_ERROR":
            print(f"    [CONN Error] {text[:100]}")
        elif status == "TIMEOUT":
            print(f"    [TIMEOUT]")
        else:
            print(f"    Texto: {text[:100]}")

    # 2. Verificar si es problema de headers
    print("\n\n[2] PROBANDO CON DIFERENTES HEADERS")
    print("=" * 70)

    test_url = f"http://{router_ip}/"
    header_variants = [
        ({}, "Sin headers"),
        ({'User-Agent': 'Mozilla/5.0'}, "Solo User-Agent"),
        ({'User-Agent': 'curl/7.0'}, "User-Agent curl"),
        ({'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}, "Headers basicos"),
        ({'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}, "Acepta JSON"),
    ]

    for headers, desc in header_variants:
        status, text = test_endpoint(test_url, headers)
        print(f"  {desc}: Status {status}")

    # 3. Resumen y recomendaciones
    print("\n" + "=" * 70)
    print("  POSIBLES CAUSAS Y SOLUCIONES")
    print("=" * 70)
    print("""
  1. EL ROUTER DEL COLEGIO ES MAS NUEVO Y USA HTTPS
     - El firmware del colegio podria ser mas reciente
     - El puerto HTTP (80) podria estar deshabilitado
     - SOLUCION: Cambiar http:// a https:// en los scripts

  2. HAY UN FIREWALL EN EL ROUTER
     - El router del colegio puede tener reglas de firewall
     - SOLUCION: Entrar al panel via navegador y desactivar
       firewall temporalmente, o agregar tu IP a la whitelist

  3. EL PUERTO 80 ESTA DESHABILITADO
     - Algunos routers permiten acceso solo por HTTPS
     - SOLUCION: Usar https:// en lugar de http://

  4. TU IP ESTA BLOQUEADA
     - El router puede tener una lista negra de IPs
     - SOLUCION: Verificar en el panel del router o resetear

  5. VERSION DE FIRMWARE DIFERENTE
     - El colegio puede tener un firmware mas restrictivo
     - SOLUCION: Verificar version en panel web del router
       y comparar con la tuya de casa

  6. CREDENCIALES CAMBIADAS
     - Si cambiaste la pass del "user" en el colegio
     - SOLUCION: Actualizar router_config.json con la nueva pass

  7. SESION ACTIVA EN OTRO LADO
     - Si alguien mas esta logueado como user
     - SOLUCION: Cerrar la otra sesion desde el panel
""")

    print("=" * 70)
    print()
    input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()