import requests
from datetime import datetime

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://192.168.1.1/main.html?6802',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
}

print("=" * 70)
print("  ESCANEANDO ENDPOINTS /fh_api/ - FIRMWARE NUEVO")
print("=" * 70)

# Endpoints comunes para este firmware
endpoints = [
    # Info basica
    "get_device_info",
    "get_base_info",
    "get_device_information",
    "get_system_info",
    "get_status",
    # WiFi
    "get_wifi_info",
    "get_wifi_status",
    "get_wifi_basic",
    "get_wifi_2g",
    "get_wifi_5g",
    "get_wifi_2g_info",
    "get_wifi_5g_info",
    "get_wifi_radio",
    "get_wifi_radio_info",
    "get_wifi_ap",
    "get_wifi_clients",
    "get_wlan_info",
    "get_wlan_status",
    # Red
    "get_network_info",
    "get_lan_info",
    "get_lan_status",
    "get_wan_info",
    "get_wan_status",
    "get_internet_info",
    # GPON
    "get_pon_info",
    "get_pon_status",
    "get_optical_info",
    "get_optical_status",
    # Dispositivos
    "get_devices",
    "get_device_list",
    "get_clients",
    "get_connected_devices",
    "get_hosts",
    "get_stations",
    "get_associated_devices",
    "get_host_info",
    # Trafico
    "get_traffic_info",
    "get_traffic_stats",
    "get_bandwidth",
    "get_data_stats",
    # System
    "get_cpu_info",
    "get_memory_info",
    "get_uptime",
    "get_version",
    "get_firmware",
    # Login/logout
    "DO_WEB_LOGIN",
    "DO_WEB_LOGOUT",
    "WEB_CHECK_LOGIN",
]

working = []
empty = []

print("\nProbando endpoints...")
print("-" * 70)

for ep in endpoints:
    url = f"http://192.168.1.1/fh_api/{ep}"
    try:
        r = session.get(url, headers=headers, timeout=5)
        text = r.text.strip()
        if r.status_code == 200 and text and text != "" and text != "1":
            try:
                data = r.json()
                working.append((ep, data))
                print(f"[OK] {ep}")
            except:
                if len(text) > 5:
                    working.append((ep, {"raw": text[:200]}))
                    print(f"[OK] {ep} (raw): {text[:100]}")
                else:
                    empty.append(ep)
                    print(f"[--] {ep} (text: {text[:50]})")
        else:
            empty.append(ep)
            status = r.status_code
            print(f"[{status}] {ep}")
    except Exception as e:
        empty.append(ep)
        print(f"[ERR] {ep}")

print()
print("=" * 70)
print(f"  ENDPOINTS ACTIVOS: {len(working)}")
print("=" * 70)

for ep, data in working:
    print(f"\n[{ep}]")
    if isinstance(data, dict):
        for k, v in list(data.items())[:8]:
            print(f"  {k}: {v}")