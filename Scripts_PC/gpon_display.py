#!/usr/bin/env python3
"""
Monitor GPON - Huawei HG6145F - Mundo Chile
Muestra trafico, uptime y sistema del router
Soporta configuracion desde archivo JSON
"""

import requests
import json
import os
import sys
import subprocess
from datetime import datetime

CONFIG_FILE = "router_config.json"

def load_config():
    """Carga configuracion desde archivo JSON"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ip": "192.168.1.1", "user": "user", "password": "user1234"}

def get_new_firmware_data(router_ip):
    config = load_config()
    helper_path = os.path.join(os.path.dirname(__file__), "router_web_client.js")

    try:
        result = subprocess.run(
            ["node", helper_path, router_ip, config.get("user", "user"), config.get("password", "user1234")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
            check=False,
        )
    except Exception as exc:
        return {
            "ModelName": "Router con firmware nuevo (RP3084+)",
            "SoftwareVersion": "N/A (helper no disponible)",
            "WANAccessType": "N/A",
            "uptime": "0",
            "cpu_usage": "0",
            "ponBytesSent": "0",
            "ponBytesReceived": "0",
            "NOTA": f"No se pudo ejecutar el helper web: {exc}",
        }

    output = (result.stdout or "").strip()
    if not output:
        return {
            "ModelName": "Router con firmware nuevo (RP3084+)",
            "SoftwareVersion": "N/A (sin salida del helper)",
            "WANAccessType": "N/A",
            "uptime": "0",
            "cpu_usage": "0",
            "ponBytesSent": "0",
            "ponBytesReceived": "0",
            "NOTA": (result.stderr or "El helper web no devolvio salida").strip(),
        }

    try:
        parsed = json.loads(output.splitlines()[-1])
    except Exception:
        return {
            "ModelName": "Router con firmware nuevo (RP3084+)",
            "SoftwareVersion": "N/A (salida invalida)",
            "WANAccessType": "N/A",
            "uptime": "0",
            "cpu_usage": "0",
            "ponBytesSent": "0",
            "ponBytesReceived": "0",
            "NOTA": output[:300],
        }

    if parsed.get("success"):
        return parsed["data"]

    return {
        "ModelName": "Router con firmware nuevo (RP3084+)",
        "SoftwareVersion": "N/A (login web fallo)",
        "WANAccessType": "N/A",
        "uptime": "0",
        "cpu_usage": "0",
        "ponBytesSent": "0",
        "ponBytesReceived": "0",
        "NOTA": parsed.get("error", "No se pudo autenticar por flujo web"),
    }

def detect_firmware(router_ip):
    """Detecta que firmware tiene el router"""
    session = requests.Session()

    # Probar firmware nuevo (RP3084+) primero
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': f'http://{router_ip}/main.html?6802',
            'X-Requested-With': 'XMLHttpRequest',
        }
        resp = session.get(
            f"http://{router_ip}/fh_api/tmp/heartbeat",
            headers=headers, timeout=3
        )
        # 200 = respondio OK, 418 = respondio pero sin sesion (router existe)
        if resp.status_code in [200, 418]:
            return "NEW", headers
    except:
        pass

    # Probar firmware viejo (RP2934)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
            'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
            'Accept': '*/*',
        }
        resp = session.get(
            f"http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_=1",
            headers=headers, timeout=3
        )
        if resp.status_code == 200 and "sessionid" in resp.text:
            return "OLD", headers
    except:
        pass

    return "UNKNOWN", None

def get_gpon_data(router_ip):
    """Obtiene datos del router, compatible con ambos firmwares"""
    session = requests.Session()
    firmware, _ = detect_firmware(router_ip)

    if firmware == "OLD":
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
            'Referer': f'http://{router_ip}/html/stateOverview_inter.html',
            'Accept': '*/*',
        }
        url = f'http://{router_ip}/cgi-bin/ajax?ajaxmethod=get_base_info&_={datetime.now().timestamp()}'
        resp = session.get(url, headers=headers, timeout=10)
        return json.loads(resp.text), "OLD"

    elif firmware == "NEW":
        return get_new_firmware_data(router_ip), "NEW"

    return None, "UNKNOWN"

def format_bytes(bytes_val):
    try:
        gb = bytes_val / (1024**3)
        if gb >= 1:
            return f"{gb:.2f} GB"
        mb = bytes_val / (1024**2)
        return f"{mb:.2f} MB"
    except:
        return str(bytes_val)

def format_number(n):
    try:
        return f"{int(n):,}"
    except:
        return str(n)

def format_uptime(seconds):
    try:
        sec = int(seconds)
        dias = sec // 86400
        horas = (sec % 86400) // 3600
        minutos = (sec % 3600) // 60
        if dias > 0:
            return f"{dias}d {horas}h {minutos}m"
        elif horas > 0:
            return f"{horas}h {minutos}m"
        else:
            return f"{minutos}m"
    except:
        return str(seconds)

def main():
    # Prioridad: argumento CLI > config file > default
    if len(sys.argv) > 1:
        router = sys.argv[1]
    else:
        config = load_config()
        router = config.get("ip", "192.168.1.1")

    print("")
    print("=" * 65)
    print("  MONITOR GPON - HUAWEI HG6145F (MUNDO CHILE)")
    print("=" * 65)
    print(f"  Router IP: {router}")
    print(f"  Fecha:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    print(f"  Detectando firmware...")
    try:
        data, firmware = get_gpon_data(router)

        if data is None:
            print(f"  [!] No se pudo detectar el firmware del router")
            print(f"  [!] Verifica que estes conectado a la red del router")
            print("=" * 65)
            return

        if firmware == "NEW" and not data.get("authenticated"):
            print(f"  [INFO] Router con firmware NUEVO detectado (RP3084+)")
            print(f"         Este firmware requiere login con AES para obtener datos")
            print(f"         Solo se puede verificar conexion (heartbeat OK)")
            print()
            print("-" * 65)
            print("  Presiona ENTER para salir...")
            return

        if firmware == "NEW":
            print(f"  [INFO] Router con firmware NUEVO detectado (RP3084+)")
            print(f"         Login web automatizado completado")
            if data.get("NOTA"):
                print(f"         Nota: {data['NOTA']}")
            print()

        uptime_sec = int(data.get('uptime', 0))
        print(f"  [UPTIME]")
        print(f"    Activo desde hace: {format_uptime(uptime_sec)}")
        print(f"    Total segundos:    {format_number(uptime_sec)}")
        print()

        pon_sent = int(data.get('ponBytesSent', 0))
        pon_recv = int(data.get('ponBytesReceived', 0))
        print(f"  [TRAFICO GPON - NO DISPONIBLE EN RP3084+]")
        print(f"    El firmware RP3084+ no expone contadores PON totales.")
        print(f"    Se usan contadores por puerto LAN y WiFi como alternativa.")
        print()

        # WiFi 5GHz counters
        wifi5_sent = int(data.get('wifi5_bytes_sent', 0) or 0)
        wifi5_recv = int(data.get('wifi5_bytes_received', 0) or 0)
        if wifi5_sent or wifi5_recv or data.get('wifi5_channel'):
            print(f"  [WIFI 5 GHZ]")
            print(f"    Canal:     {data.get('wifi5_channel', 'N/A')}")
            print(f"    Estandar:  {data.get('wifi5_standard', 'N/A')}")
            if data.get('wifi5_ssid_1'):
                print(f"    SSID1:     {data.get('wifi5_ssid_1', 'N/A')}")
            if data.get('wifi5_ssid_2'):
                print(f"    SSID2:     {data.get('wifi5_ssid_2', 'N/A')}")
            print(f"    Enviado:   {format_bytes(wifi5_sent)} ({format_number(wifi5_sent)} bytes)")
            print(f"    Recibido:  {format_bytes(wifi5_recv)} ({format_number(wifi5_recv)} bytes)")
            print()

        # WiFi 2.4GHz counters
        wifi24_sent = int(data.get('wifi24_bytes_sent', 0) or 0)
        wifi24_recv = int(data.get('wifi24_bytes_received', 0) or 0)
        if wifi24_sent or wifi24_recv or data.get('wifi24_channel'):
            print(f"  [WIFI 2.4 GHZ]")
            print(f"    Canal:     {data.get('wifi24_channel', 'N/A')}")
            print(f"    Estandar:  {data.get('wifi24_standard', 'N/A')}")
            if data.get('wifi24_ssid_1'):
                print(f"    SSID1:     {data.get('wifi24_ssid_1', 'N/A')}")
            if data.get('wifi24_ssid_2'):
                print(f"    SSID2:     {data.get('wifi24_ssid_2', 'N/A')}")
            print(f"    Enviado:   {format_bytes(wifi24_sent)} ({format_number(wifi24_sent)} bytes)")
            print(f"    Recibido:  {format_bytes(wifi24_recv)} ({format_number(wifi24_recv)} bytes)")
            print()

        # LAN port counters
        has_lan = any(data.get(f'lan{i}_bytes_sent', None) is not None for i in range(1, 10))
        if has_lan:
            print(f"  [LAN PORTS]")
            for i in range(1, 10):
                status = data.get(f'lan{i}_status', '')
                if not status:
                    continue
                sent = int(data.get(f'lan{i}_bytes_sent', 0) or 0)
                recv = int(data.get(f'lan{i}_bytes_received', 0) or 0)
                speed = data.get(f'lan{i}_speed', '')
                if sent or recv or status == 'Up':
                    print(f"    Port {i}: {status} ({speed})")
                    if sent or recv:
                        print(f"      Enviado:   {format_bytes(sent)} ({format_number(sent)} bytes)")
                        print(f"      Recibido:  {format_bytes(recv)} ({format_number(recv)} bytes)")
            print()

        cpu = data.get('cpu_usage', 'N/A')
        mem_total = int(data.get('mem_total', 0))
        mem_free = int(data.get('mem_free', 0))
        mem_used = mem_total - mem_free
        mem_pct = (mem_used / mem_total * 100) if mem_total > 0 else 0
        print(f"  [SISTEMA]")
        print(f"    CPU:  {cpu}%")
        print(f"    RAM:  {format_bytes(mem_used)} / {format_bytes(mem_total)} ({mem_pct:.1f}%)")
        print(f"    Modelo:     {data.get('ModelName', 'N/A')}")
        print(f"    Firmware:   {data.get('SoftwareVersion', 'N/A')}")
        print()

        print(f"  [SENAL OPTICA]")
        print(f"    Tx Power:    {data.get('txpower', 'N/A')} dBm")
        print(f"    Rx Power:    {data.get('rxpower', 'N/A')} dBm")
        print(f"    Temperatura: {data.get('transceivertemperature', 'N/A')} C")
        print(f"    Voltaje:     {data.get('supplyvottage', 'N/A')} V")
        print(f"    Corriente:   {data.get('biascurrent', 'N/A')} mA")
        print()

        print(f"  [WAN]")
        print(f"    Tipo:       {data.get('WANAccessType', 'N/A')}")
        print(f"    PON Status: {data.get('pon_reg_state', 'N/A')}")
        tr069 = "Activo" if data.get('tr069ipstatus') == '1' else "Inactivo"
        print(f"    TR-069:     {tr069}")

        print("-" * 65)
        print("  Tip: Para cambiar la IP, edita router_config.json")
        print("       o usa la opcion 4 del menu principal (Monitor_GPON.bat)")

    except Exception as e:
        print(f"  [!] Error: {e}")
        print(f"  [!] Verifica la IP del router ({router})")
        print(f"  [!] Y que estes conectado a la red del router")

    print("=" * 65)
    print()
    try:
        input("  Presiona ENTER para salir...")
    except:
        pass

if __name__ == "__main__":
    main()
