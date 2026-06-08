#!/usr/bin/env python3
"""
Monitoreo continuo del router GPON
Guarda datos cada minuto en archivo de log
Uso: python gpon_monitor.py [IP]
Si no se pasa IP, usa la configuracion guardada
"""

import requests
import json
import os
import sys
import time
from datetime import datetime

CONFIG_FILE = "router_config.json"
LOG_FILE = "traffic_log.txt"
LAST_SAMPLE = None

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

def calculate_rate(sent, recv):
    global LAST_SAMPLE
    now = datetime.now()
    rate = None

    if LAST_SAMPLE:
        seconds = (now - LAST_SAMPLE["timestamp"]).total_seconds()
        sent_delta = sent - LAST_SAMPLE["sent"]
        recv_delta = recv - LAST_SAMPLE["recv"]
        if seconds > 0 and sent_delta >= 0 and recv_delta >= 0:
            rate = {
                "sent_mbps": sent_delta * 8 / seconds / 1_000_000,
                "recv_mbps": recv_delta * 8 / seconds / 1_000_000,
                "total_mbps": (sent_delta + recv_delta) * 8 / seconds / 1_000_000,
                "seconds": seconds,
            }

    LAST_SAMPLE = {"timestamp": now, "sent": sent, "recv": recv}
    return rate

def format_mbps(value):
    if value >= 1000:
        return f"{value / 1000:.2f} Gbps"
    return f"{value:.2f} Mbps"

def save_data(data, router_ip, rate):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sent = int(data.get('ponBytesSent', 0))
    recv = int(data.get('ponBytesReceived', 0))
    cpu = data.get('cpu_usage', 'N/A')
    uptime = int(data.get('uptime', 0))

    rate_text = "Rate: N/A"
    if rate:
        rate_text = (f"Rate: total {format_mbps(rate['total_mbps'])}, "
                     f"up {format_mbps(rate['sent_mbps'])}, down {format_mbps(rate['recv_mbps'])}, "
                     f"interval {rate['seconds']:.1f}s")

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{ts} | {router_ip} | Sent: {format_bytes(sent)} ({sent}) | "
                f"Recv: {format_bytes(recv)} ({recv}) | {rate_text} | CPU: {cpu}% | "
                f"Uptime: {uptime}s\n")

def print_data(data, router_ip, rate):
    sent = int(data.get('ponBytesSent', 0))
    recv = int(data.get('ponBytesReceived', 0))
    uptime = int(data.get('uptime', 0))
    cpu = data.get('cpu_usage', 'N/A')
    temp = data.get('transceivertemperature', 'N/A')

    print("\n" + "=" * 65)
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Router: {router_ip}")
    print("=" * 65)
    print(f"  Uptime:      {uptime // 3600}h {(uptime % 3600) // 60}m")
    print(f"  GPON Enviado:  {format_bytes(sent)} ({sent:,} b)")
    print(f"  GPON Recibido: {format_bytes(recv)} ({recv:,} b)")
    if rate:
        print(f"  Ancho banda:   {format_mbps(rate['total_mbps'])} total "
              f"({format_mbps(rate['sent_mbps'])} subida / {format_mbps(rate['recv_mbps'])} bajada)")
    else:
        print("  Ancho banda:   esperando 2 lecturas")
    print(f"  CPU:         {cpu}%")
    print(f"  Temperatura: {temp} C")
    print("=" * 65)

def main():
    if len(sys.argv) > 1:
        router = sys.argv[1]
    else:
        router = load_config().get("ip", "192.168.1.1")

    # Crear archivo de log con header
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# Monitor GPON - {router}\n")
            f.write("# Formato: timestamp | IP | Sent | Recv | Rate | CPU | Uptime\n")
            f.write("# Rate se calcula desde contadores GPON del router; no mide trafico del PC.\n")
            f.write("-" * 80 + "\n")

    print(f"Monitoreo continuo del router {router}")
    print(f"Log guardado en: {LOG_FILE}")
    print("Presione Ctrl+C para detener")
    print()

    try:
        while True:
            try:
                data = get_data(router)
                sent = int(data.get('ponBytesSent', 0))
                recv = int(data.get('ponBytesReceived', 0))
                rate = calculate_rate(sent, recv)
                print_data(data, router, rate)
                save_data(data, router, rate)
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nDetenido por usuario")

if __name__ == "__main__":
    main()
