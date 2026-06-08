import requests
from datetime import datetime

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://192.168.1.1/main.html?5685',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': '*/*',
}

print("=" * 70)
print("  PROBANDO ENDPOINTS DESCUBIERTOS")
print("=" * 70)

# Probar varios endpoints
endpoints = [
    # FHAPIS - el endpoint principal
    ("GET", "/fh_api/tmp/FHAPIS?ajaxmethod=is_encrypt&_=0.1", None),
    ("GET", "/fh_api/tmp/FHAPIS?ajaxmethod=get_refresh_sessionid&_=0.1", None),
    ("GET", "/fh_api/FHAPIS?ajaxmethod=is_encrypt&_=0.1", None),
    ("GET", "/fh_api/FHAPIS?ajaxmethod=get_refresh_sessionid&_=0.1", None),
    # FHNCAPIS
    ("GET", "/fh_api/FHNCAPIS?ajaxmethod=is_encrypt&_=0.1", None),
    ("GET", "/fh_api/FHNCAPIS?ajaxmethod=get_refresh_sessionid&_=0.1", None),
    # POST sin data
    ("POST", "/fh_api/tmp/FHAPIS", "ajaxmethod=is_encrypt"),
    ("POST", "/fh_api/tmp/FHAPIS", "ajaxmethod=get_refresh_sessionid"),
]

for method, path, body in endpoints:
    url = f"http://192.168.1.1{path}"
    try:
        if method == "GET":
            resp = session.get(url, headers=headers, timeout=5)
        else:
            resp = session.post(url, data=body, headers=headers, timeout=5)
        print(f"\n[{method}] {path}")
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {resp.text[:300]}")
        else:
            print(f"  Response: {resp.text[:100]}")
    except Exception as e:
        print(f"\n[{method}] {path}")
        print(f"  Error: {e}")

# Intentar el endpoint FHAPIS con sessionid
print("\n" + "=" * 70)
print("  PROBANDO DO_WEB_LOGIN con FHAPIS")
print("=" * 70)

# Primero obtener sessionid
url = "http://192.168.1.1/fh_api/tmp/FHAPIS?ajaxmethod=get_refresh_sessionid&_=0.1"
resp = session.get(url, headers=headers, timeout=5)
print(f"\nget_refresh_sessionid: {resp.status_code} - {resp.text[:200]}")

# Intentar login
url = "http://192.168.1.1/fh_api/tmp/FHAPIS?ajaxmethod=do_login&_=0.2"
data = {"yhm": "user", "mm": "user1234"}
resp = session.post(url, data=data, headers=headers, timeout=5)
print(f"\ndo_login: {resp.status_code} - {resp.text[:300]}")