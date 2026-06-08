#!/usr/bin/env python3
"""
Consulta rapida del router GPON
Uso: python gpon_check.py [IP]
Si no se pasa IP, usa la configuracion guardada
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
    return {"ip": "192.168.1.1"}

def get_data(router_ip):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
        'Accept': '*/*',
    }
    url = f'http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_={datetime.now().timestamp()}'
    resp = session.get(url, headers=headers, timeout=10)
    return json.loads(resp.text)

def format_bytes(b):
    gb = b / (1024**3)
    if gb >= 1:
        return f"{gb:.2f} GB"
    return f"{b / (1024**2):.2f} MB"

def format_uptime(s):
    s = int(s)
    d = s // 86400
    h = (s % 86400) // 3600
    m = (s % 3600) // 60
    if d > 0:
        return f"{d}d {h}h {m}m"
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def main():
    if len(sys.argv) > 1:
        router = sys.argv[1]
    else:
        router = load_config().get("ip", "192.168.1.1")

    try:
        data = get_data(router)
        sent = int(data.get('ponBytesSent', 0))
        recv = int(data.get('ponBytesReceived', 0))
        uptime = int(data.get('uptime', 0))

        print(f"""
============================================
  GPON - {router} - {datetime.now().strftime('%H:%M:%S')}
============================================
  Uptime:   {format_uptime(uptime)}
  Enviado:  {format_bytes(sent)} ({sent:,} b)
  Recibido: {format_bytes(recv)} ({recv:,} b)
  Total:    {format_bytes(sent + recv)}
============================================
""")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Verifica la IP {router} y tu conexion al router")

if __name__ == "__main__":
    main()