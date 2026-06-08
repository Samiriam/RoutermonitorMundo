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
        # Firmware nuevo - solo podemos verificar que esta vivo
        return {
            "ModelName": "Router con firmware nuevo (RP3084+)",
            "SoftwareVersion": "N/A (requiere login)",
            "WANAccessType": "N/A (requiere login)",
            "uptime": "0",
            "cpu_usage": "0",
            "ponBytesSent": "0",
            "ponBytesReceived": "0",
            "NOTA": "Este firmware requiere login con AES para obtener datos"
        }, "NEW"

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

        if firmware == "NEW":
            print(f"  [INFO] Router con firmware NUEVO detectado (RP3084+)")
            print(f"         Este firmware requiere login con AES para obtener datos")
            print(f"         Solo se puede verificar conexion (heartbeat OK)")
            print()
            print("-" * 65)
            print("  Presiona ENTER para salir...")
            return

        uptime_sec = int(data.get('uptime', 0))
        print(f"  [UPTIME]")
        print(f"    Activo desde hace: {format_uptime(uptime_sec)}")
        print(f"    Total segundos:    {format_number(uptime_sec)}")
        print()

        pon_sent = int(data.get('ponBytesSent', 0))
        pon_recv = int(data.get('ponBytesReceived', 0))
        print(f"  [TRAFICO GPON]")
        print(f"    Enviado:   {format_bytes(pon_sent)} ({format_number(pon_sent)} bytes)")
        print(f"    Recibido:  {format_bytes(pon_recv)} ({format_number(pon_recv)} bytes)")
        print(f"    Total:     {format_bytes(pon_sent + pon_recv)}")
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