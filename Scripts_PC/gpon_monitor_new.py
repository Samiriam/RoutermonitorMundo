#!/usr/bin/env python3
"""
Monitoreo continuo del router - Soporta ambos firmwares
RP2934 (HG6145F): via get_base_info (ponBytes)
RP3084+ (HG5853SF): via Playwright helper (LAN por puerto + WiFi)
"""

import json
import os
import subprocess
import time
import requests
from datetime import datetime

CONFIG_FILE = "router_config.json"
LOG_FILE = "traffic_log.txt"

_last_sample = None

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ip": "192.168.1.1", "user": "user", "password": "user1234"}

def fmt_bytes(b):
    try:
        b = int(b)
        if b >= 1024**4: return f"{b / 1024**4:.2f} TB"
        if b >= 1024**3: return f"{b / 1024**3:.2f} GB"
        if b >= 1024**2: return f"{b / 1024**2:.2f} MB"
        if b >= 1024: return f"{b / 1024:.2f} KB"
        return f"{b} B"
    except:
        return str(b)

def fmt_bw(mbps):
    if mbps >= 1000: return f"{mbps / 1000:.2f} Gbps"
    return f"{mbps:.2f} Mbps"

def detect_firmware(router_ip):
    try:
        resp = requests.get(
            f"http://{router_ip}/fh_api/tmp/heartbeat",
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': f'http://{router_ip}/main.html'},
            timeout=3
        )
        if resp.status_code in [200, 418]:
            return "NEW"
    except:
        pass
    try:
        resp = requests.get(
            f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_=1",
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': f'http://{router_ip}/html/stateOverview_inter.html'},
            timeout=3
        )
        if resp.status_code == 200 and "sessionid" in resp.text:
            return "OLD"
    except:
        pass
    return "UNKNOWN"

def get_old_firmware_data(router_ip):
    url = f'http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_={datetime.now().timestamp()}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
        'Accept': '*/*',
    }
    resp = requests.get(url, headers=headers, timeout=10)
    return json.loads(resp.text)

def get_new_firmware_data(router_ip):
    config = load_config()
    helper_path = os.path.join(os.path.dirname(__file__), "router_web_client.js")
    result = subprocess.run(
        ["node", helper_path, router_ip, config.get("user", "user"), config.get("password", "user1234")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, check=False,
    )
    output = (result.stdout or "").strip()
    if not output:
        return {"error": (result.stderr or "sin salida").strip()}
    parsed = json.loads(output.splitlines()[-1])
    if parsed.get("success"):
        return parsed["data"]
    return {"error": parsed.get("error", "fallo login web")}

def extract_counters(data, firmware):
    counters = {}
    if firmware == "OLD":
        counters["ponBytesSent"] = int(data.get("ponBytesSent", 0))
        counters["ponBytesReceived"] = int(data.get("ponBytesReceived", 0))
    else:
        for i in range(1, 10):
            sent = data.get(f"lan{i}_bytes_sent")
            status = data.get(f"lan{i}_status", "")
            if sent is not None and status == "Up":
                counters[f"lan{i}_bytes_sent"] = int(sent)
                counters[f"lan{i}_bytes_received"] = int(data.get(f"lan{i}_bytes_received", 0))
        if data.get("wifi24_bytes_sent") is not None:
            counters["wifi24_bytes_sent"] = int(data["wifi24_bytes_sent"])
            counters["wifi24_bytes_received"] = int(data["wifi24_bytes_received"])
        if data.get("wifi5_bytes_sent") is not None:
            counters["wifi5_bytes_sent"] = int(data["wifi5_bytes_sent"])
            counters["wifi5_bytes_received"] = int(data["wifi5_bytes_received"])
    return counters

def calculate_rates(current, firmware):
    global _last_sample
    now = datetime.now()
    rates = {}

    if _last_sample and _last_sample["firmware"] == firmware:
        seconds = (now - _last_sample["timestamp"]).total_seconds()
        if seconds > 0:
            for key, cur_val in current.items():
                prev_val = _last_sample["counters"].get(key)
                if prev_val is not None:
                    delta = cur_val - prev_val
                    if delta >= 0:
                        mbps = delta * 8 / seconds / 1_000_000
                        rates[key] = {"delta": delta, "mbps": mbps, "sec": round(seconds)}

    _last_sample = {"timestamp": now, "firmware": firmware, "counters": current}
    return rates

def show(router_ip, data, firmware, counters, rates):
    uptime = int(data.get("uptime", 0))
    cpu = data.get("cpu_usage", "N/A")
    ts = datetime.now()

    print(f"\n{'='*70}")
    print(f"  {ts.strftime('%Y-%m-%d %H:%M:%S')} - {router_ip} [{firmware}]")
    print(f"  Vivo {uptime//86400}d {(uptime%86400)//3600}h {(uptime%3600)//60}m | CPU {cpu}%")
    print(f"{'='*70}")

    if firmware == "OLD":
        s = counters.get("ponBytesSent", 0)
        r = counters.get("ponBytesReceived", 0)
        print(f"  GPON TX: {fmt_bytes(s)} | RX: {fmt_bytes(r)}")
        rs = rates.get("ponBytesSent")
        if rs:
            print(f"  BW   TX: {fmt_bw(rs['mbps'])} | RX: {fmt_bw(rates['ponBytesReceived']['mbps'])}")
    else:
        for i in range(1, 10):
            s = counters.get(f"lan{i}_bytes_sent")
            if s is None:
                continue
            r = counters.get(f"lan{i}_bytes_received", 0)
            st = data.get(f"lan{i}_status", "")
            sp = data.get(f"lan{i}_speed", "")
            line = f"  LAN{i} ({sp}, {st}) TX {fmt_bytes(s)} RX {fmt_bytes(r)}"
            rs = rates.get(f"lan{i}_bytes_sent")
            if rs:
                line += f" | TX {fmt_bw(rs['mbps'])} RX {fmt_bw(rates[f'lan{i}_bytes_received']['mbps'])}"
            print(line)

        for band, label in [("wifi24", "2.4G"), ("wifi5", "5G")]:
            s = counters.get(f"{band}_bytes_sent")
            if s is None:
                continue
            r = counters.get(f"{band}_bytes_received", 0)
            ssid = data.get(f"{band}_ssid_1", label)
            ch = data.get(f"{band}_channel", "")
            line = f"  WiFi {label} ({ssid}, CH{ch}) TX {fmt_bytes(s)} RX {fmt_bytes(r)}"
            rs = rates.get(f"{band}_bytes_sent")
            if rs:
                line += f" | TX {fmt_bw(rs['mbps'])} RX {fmt_bw(rates[f'{band}_bytes_received']['mbps'])}"
            print(line)

        print(f"  --- Los contadores son por interfaz (total PON no expuesto en RP3084+)")

def log(router_ip, data, firmware, counters, rates):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"\n--- {ts} | {router_ip} | {firmware} ---"]

    for k, v in counters.items():
        lines.append(f"{k}: {v} ({fmt_bytes(v)})")

    if rates:
        for k, r in rates.items():
            lines.append(f"{k}: +{r['delta']} ({fmt_bytes(r['delta'])}) en {r['sec']}s = {fmt_bw(r['mbps'])}")

    cpu = data.get("cpu_usage", "N/A")
    uptime = data.get("uptime", "0")
    lines.append(f"CPU: {cpu}% | Uptime: {uptime}s")

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

def main():
    config = load_config()
    router_ip = config.get("ip", "192.168.1.1")

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# Router Monitor - {router_ip} - {datetime.now()}\n")

    print(f"Monitoreando {router_ip} cada 60s (Ctrl+C detiene)")

    detected = False
    firmware = None

    while True:
        try:
            if not detected:
                firmware = detect_firmware(router_ip)
                if firmware == "UNKNOWN":
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Router no detectado, reintentando en 10s...")
                    time.sleep(10)
                    continue
                detected = True
                print(f"Firmware: {firmware}")

            if firmware == "OLD":
                data = get_old_firmware_data(router_ip)
            else:
                data = get_new_firmware_data(router_ip)
                if "error" in data:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {data['error']}")
                    time.sleep(30)
                    continue

            counters = extract_counters(data, firmware)
            rates = calculate_rates(counters, firmware)
            log(router_ip, data, firmware, counters, rates)
            show(router_ip, data, firmware, counters, rates)

        except KeyboardInterrupt:
            print("\nDetenido")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
