import requests
import json
from datetime import datetime

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://192.168.1.1/main.html?5685',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': '*/*',
}

# 1. Obtener sessionid
print("=" * 70)
print("  PASO 1: Obtener sessionid")
print("=" * 70)
url = "http://192.168.1.1/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid"
resp = session.get(url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
data = json.loads(resp.text)
session_id = data.get("sessionid")
print(f"Session ID: {session_id}")

# 2. Probar login con sessionid
print("\n" + "=" * 70)
print("  PASO 2: Probar login con diferentes metodos")
print("=" * 70)

login_attempts = [
    # Plain text
    ("POST", "FHNCAPIS", {"yhm": "user", "mm": "user1234", "sessionid": session_id}),
    ("POST", "FHAPIS", {"yhm": "user", "mm": "user1234", "sessionid": session_id}),
    ("GET", "FHNCAPIS", {"ajaxmethod": "do_login", "yhm": "user", "mm": "user1234", "sessionid": session_id}),
    # AES-like encoding
    ("POST", "FHNCAPIS", {"yhm": "user", "mm": "user1234", "sessionid": session_id, "is_encrypt": "1"}),
    # With do_login method
    ("POST", "FHNCAPIS", {"ajaxmethod": "do_login", "yhm": "user", "mm": "user1234", "sessionid": session_id}),
]

for method, endpoint, data in login_attempts:
    if method == "POST":
        if "FHNCAPIS" in endpoint:
            url = f"http://192.168.1.1/fh_api/tmp/{endpoint}"
        else:
            url = f"http://192.168.1.1/fh_api/{endpoint}"
    else:
        url = f"http://192.168.1.1/fh_api/tmp/{endpoint}?ajaxmethod=do_login&_=0.2"

    try:
        if method == "POST":
            resp = session.post(url, data=data, headers=headers, timeout=5)
        else:
            resp = session.get(url, headers=data, headers=headers, timeout=5)
        print(f"\n[{method}] {endpoint}")
        print(f"  Data: {data}")
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {resp.text[:300]}")
        else:
            print(f"  Response: {resp.text[:100]}")
    except Exception as e:
        print(f"\n[{method}] {endpoint}: ERROR - {e}")

# 3. Probar is_encrypt para ver si la encriptacion es requerida
print("\n" + "=" * 70)
print("  PASO 3: Verificar is_encrypt")
print("=" * 70)
url = "http://192.168.1.1/fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt"
resp = session.get(url, headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:200]}")

# 4. Probar endpoint do_login (nombre real)
print("\n" + "=" * 70)
print("  PASO 4: Probar do_login")
print("=" * 70)
url = "http://192.168.1.1/fh_api/tmp/FHNCAPIS?ajaxmethod=do_login"
data = {"yhm": "user", "mm": "user1234", "sessionid": session_id}
resp = session.post(url, data=data, headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:300]}")

# 5. Probar get_base_info
print("\n" + "=" * 70)
print("  PASO 5: Probar get_base_info")
print("=" * 70)
url = "http://192.168.1.1/fh_api/tmp/FHNCAPIS?ajaxmethod=get_base_info"
resp = session.get(url, headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:300]}")