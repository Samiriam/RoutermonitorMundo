#!/usr/bin/env python3
"""
Monitor GPON - Mundo Chile
Aplicacion de escritorio para monitorear routers Huawei/FiberHome de Mundo Chile.
Interfaz grafica moderna (tema oscuro) con configuracion de IP, usuario y password.
Funciona con:
  - Firmware antiguo (HG6145F): endpoint /cgi-bin/ajax -> get_base_info (GPON nativo)
  - Firmware RP3084+ (HG5853SF): helper web con Playwright (LAN + WiFi + optica)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import threading
from datetime import datetime
import os
import sys
import json as json_lib
import subprocess

CONFIG_FILE = "router_config.json"

# ---------------------------------------------------------------- paleta
COL_BG        = "#0f172a"   # fondo principal
COL_PANEL     = "#1e293b"   # paneles / label frames
COL_PANEL_2   = "#334155"   # inputs / hover
COL_BORDER    = "#334155"
COL_TEXT      = "#e2e8f0"   # texto principal
COL_MUTED     = "#94a3b8"   # texto secundario
COL_ACCENT    = "#38bdf8"   # azul acento
COL_ACCENT_D  = "#0ea5e9"
COL_GREEN     = "#4ade80"
COL_AMBER     = "#fbbf24"
COL_ORANGE    = "#fb923c"
COL_RED       = "#f87171"
COL_HEADING   = "#0ea5e9"

FONT_H1   = ("Segoe UI", 20, "bold")
FONT_H2   = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SMALL= ("Segoe UI", 9)


class RouterMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor GPON - Mundo Chile")
        self.root.geometry("1000x720")
        self.root.minsize(860, 600)
        self.root.configure(bg=COL_BG)

        self.config = self.load_config()

        self.router_ip = tk.StringVar(value=self.config.get("ip", "192.168.1.1"))
        self.username = tk.StringVar(value=self.config.get("user", "user"))
        self.password = tk.StringVar(value=self.config.get("password", "user1234"))
        self.api_path = tk.StringVar(value=self.config.get("api_path", "/cgi-bin/ajax"))
        self.ajax_method = tk.StringVar(value=self.config.get("ajax_method", "get_base_info"))
        self.auto_refresh = tk.BooleanVar(value=False)
        self.last_data = None
        self.last_update = None
        self.traffic_samples = []
        self.current_rate = None
        self.min_rate = None
        self.max_rate = None

        self._configure_style()
        self.auto_refresh_id = None
        self.create_widgets()
        self._set_status("Listo - configure el router y presione Actualizar", COL_GREEN)

    # ------------------------------------------------------------ estilo
    def _configure_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background=COL_BG)
        style.configure("Card.TFrame", background=COL_PANEL)

        style.configure("TLabel", background=COL_BG, foreground=COL_TEXT, font=FONT_BODY)
        style.configure("Muted.TLabel", background=COL_BG, foreground=COL_MUTED, font=FONT_SMALL)
        style.configure("Card.TLabel", background=COL_PANEL, foreground=COL_TEXT, font=FONT_BODY)

        style.configure("Hero.TLabel", background=COL_BG, foreground=COL_TEXT, font=FONT_H1)
        style.configure("Sub.Hero.TLabel", background=COL_BG, foreground=COL_MUTED, font=FONT_SMALL)
        style.configure("Section.TLabel", background=COL_BG, foreground=COL_ACCENT, font=FONT_H2)

        style.configure("Card.TLabelframe", background=COL_PANEL, foreground=COL_TEXT, bordercolor=COL_BORDER, relief="flat")
        style.configure("Card.TLabelframe.Label", background=COL_PANEL, foreground=COL_ACCENT, font=FONT_H2)

        style.configure("TEntry", fieldbackground=COL_PANEL_2, foreground=COL_TEXT,
                        insertcolor=COL_TEXT, bordercolor=COL_BORDER, lightcolor=COL_BORDER,
                        darkcolor=COL_BORDER, padding=6)

        style.configure("Accent.TButton", background=COL_ACCENT_D, foreground="#0f172a",
                        font=("Segoe UI", 10, "bold"), padding=(14, 8), borderwidth=0)
        style.map("Accent.TButton", background=[("active", COL_ACCENT), ("pressed", COL_ACCENT_D)])

        style.configure("Ghost.TButton", background=COL_PANEL_2, foreground=COL_TEXT,
                        font=("Segoe UI", 10), padding=(12, 8), borderwidth=0)
        style.map("Ghost.TButton", background=[("active", COL_BORDER)])

        style.configure("Treeview", background=COL_PANEL, fieldbackground=COL_PANEL,
                        foreground=COL_TEXT, rowheight=26, bordercolor=COL_BORDER)
        style.configure("Treeview.Heading", background=COL_PANEL_2, foreground=COL_ACCENT,
                        font=("Segoe UI", 10, "bold"), relief="flat", padding=6)
        style.map("Treeview", background=[("selected", COL_ACCENT_D)],
                  foreground=[("selected", "#0f172a")])

    # ------------------------------------------------------------ config
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json_lib.load(f)
            except Exception:
                pass
        return {}

    def save_config(self):
        config = {
            "ip": self.router_ip.get(),
            "user": self.username.get(),
            "password": self.password.get(),
            "api_path": self.api_path.get(),
            "ajax_method": self.ajax_method.get(),
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json_lib.dump(config, f, indent=2)
            self._set_status("Configuracion guardada", COL_GREEN)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            return False

    # ------------------------------------------------------------ ui
    def create_widgets(self):
        outer = ttk.Frame(self.root, padding=(16, 12))
        outer.pack(fill="both", expand=True)

        # Cabecera
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Monitor GPON", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(header, text="Monitoreo de trafico y estado del router proximo",
                  style="Sub.Hero.TLabel").pack(anchor="w")

        # Panel configuracion
        cfg = ttk.LabelFrame(outer, text="Configuracion del Router", style="Card.TLabelframe", padding=12)
        cfg.pack(fill="x", pady=(0, 6))

        # fila 0
        ttk.Label(cfg, text="IP del Router", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(4, 8), pady=4)
        ttk.Entry(cfg, textvariable=self.router_ip, width=18).grid(row=0, column=1, padx=(0, 16), pady=4, sticky="ew")
        ttk.Label(cfg, text="Usuario", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=(4, 8), pady=4)
        ttk.Entry(cfg, textvariable=self.username, width=14).grid(row=0, column=3, padx=(0, 16), pady=4, sticky="ew")

        # fila 1
        ttk.Label(cfg, text="Password", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=(4, 8), pady=4)
        self.password_entry = ttk.Entry(cfg, textvariable=self.password, width=18, show="*")
        self.password_entry.grid(row=1, column=1, padx=(0, 16), pady=4, sticky="ew")
        ttk.Label(cfg, text="Ruta API", style="Card.TLabel").grid(row=1, column=2, sticky="w", padx=(4, 8), pady=4)
        ttk.Entry(cfg, textvariable=self.api_path, width=14).grid(row=1, column=3, padx=(0, 16), pady=4, sticky="ew")
        ttk.Label(cfg, text="Metodo AJAX", style="Card.TLabel").grid(row=1, column=4, sticky="w", padx=(4, 8), pady=4)
        ttk.Entry(cfg, textvariable=self.ajax_method, width=14).grid(row=1, column=5, pady=4, sticky="ew")

        cfg.columnconfigure(1, weight=1)
        cfg.columnconfigure(3, weight=1)
        cfg.columnconfigure(5, weight=1)

        # Botones
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=6)
        ttk.Button(actions, text="Actualizar", style="Accent.TButton", command=self.refresh_data).pack(side="left", padx=(0, 8))
        self.auto_btn = ttk.Button(actions, text="Auto (60s)", style="Ghost.TButton", command=self.toggle_auto)
        self.auto_btn.pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Mostrar/Ocultar pass", style="Ghost.TButton", command=self.toggle_password).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Guardar", style="Ghost.TButton", command=self.save_config).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Limpiar", style="Ghost.TButton", command=self.clear_data).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Exportar Reporte", style="Ghost.TButton", command=self.save_log).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Salir", style="Ghost.TButton", command=self.root.quit).pack(side="right")

        self.status_label = tk.Label(actions, text="", font=FONT_BODY, bg=COL_BG)
        self.status_label.pack(side="right", padx=16)

        # Datos
        dato = ttk.LabelFrame(outer, text="Datos del Router", style="Card.TLabelframe", padding=6)
        dato.pack(fill="both", expand=True)

        columns = ("parametro", "valor")
        self.tree = ttk.Treeview(dato, columns=columns, show="headings", height=20)
        self.tree.heading("parametro", text="Parametro")
        self.tree.heading("valor", text="Valor")
        self.tree.column("parametro", width=360, anchor="w")
        self.tree.column("valor", width=480, anchor="w")

        scrollbar = ttk.Scrollbar(dato, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # tags para colorear secciones y valores
        self.tree.tag_configure("seccion", foreground=COL_ACCENT, font=("Segoe UI", 10, "bold"), background=COL_PANEL_2)
        self.tree.tag_configure("valor", foreground=COL_TEXT)
        self.tree.tag_configure("verde", foreground=COL_GREEN)
        self.tree.tag_configure("ambar", foreground=COL_AMBER)
        self.tree.tag_configure("naranja", foreground=COL_ORANGE)
        self.tree.tag_configure("rojo", foreground=COL_RED)
        self.tree.tag_configure("mut", foreground=COL_MUTED)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _set_status(self, text, color):
        self.status_label.config(text=text, fg=color)

    def _add_seccion(self, texto):
        self.tree.insert("", "end", values=(texto, ""), tags=("seccion",))

    def _add(self, k, v, tag="valor"):
        self.tree.insert("", "end", values=(k, v), tags=(tag,))

    def toggle_password(self):
        if self.password_entry.cget("show") == "*":
            self.password_entry.config(show="")
            self._set_status("Password visible", COL_AMBER)
        else:
            self.password_entry.config(show="*")
            self._set_status("Password oculto", COL_MUTED)

    # ------------------------------------------------------------ red
    def get_data(self):
        ip = self.router_ip.get()
        api_path = self.api_path.get().strip() or "/cgi-bin/ajax"
        if not api_path.startswith("/"):
            api_path = f"/{api_path}"
        ajax_method = self.ajax_method.get().strip() or "get_base_info"
        url = f"http://{ip}{api_path}?ajaxmethod={ajax_method}&_={datetime.now().timestamp()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'http://{ip}/html/stateOverview_inter.html',
            'Accept': '*/*',
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                data["firmwareMode"] = "OLD"
                return data
        except Exception as e:
            legacy_error = str(e)
        else:
            legacy_error = f"HTTP {resp.status_code}"

        return self.get_new_firmware_data(ip, legacy_error)

    def _helper_path(self):
        # En PyInstaller onefile el helper se extrae a sys._MEIPASS;
        # en script normal, la ruta es junto a este archivo.
        if hasattr(sys, "_MEIPASS"):
            cand = os.path.join(sys._MEIPASS, "router_web_client.js")
            if os.path.exists(cand):
                return cand
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "router_web_client.js")

    def get_new_firmware_data(self, ip, legacy_error):
        helper_path = self._helper_path()
        try:
            result = subprocess.run(
                ["node", helper_path, ip, self.username.get(), self.password.get()],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=90,
                check=False,
            )
        except Exception as exc:
            return {"error": f"Endpoint antiguo fallo ({legacy_error}) y helper RP3084+ no disponible: {exc}"}

        output = (result.stdout or "").strip()
        if not output:
            error = (result.stderr or "El helper web no devolvio salida").strip()
            return {"error": f"Endpoint antiguo fallo ({legacy_error}); RP3084+ fallo: {error}"}

        try:
            parsed = json.loads(output.splitlines()[-1])
        except Exception:
            return {"error": f"Endpoint antiguo fallo ({legacy_error}); salida RP3084+ invalida: {output[:200]}"}

        if not parsed.get("success"):
            return {"error": f"Endpoint antiguo fallo ({legacy_error}); RP3084+ fallo: {parsed.get('error', 'login web fallo')}"}

        data = parsed["data"]
        data["firmwareMode"] = "NEW"
        return data

    def parse_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def record_traffic_sample(self, data):
        now = datetime.now()
        sent, recv = self.get_display_traffic_bytes(data)
        rate = None

        if self.traffic_samples:
            previous = self.traffic_samples[-1]
            seconds = (now - previous["timestamp"]).total_seconds()
            sent_delta = sent - previous["sent_bytes"]
            recv_delta = recv - previous["received_bytes"]

            if seconds > 0 and sent_delta >= 0 and recv_delta >= 0:
                rate = {
                    "timestamp": now,
                    "sent_mbps": sent_delta * 8 / seconds / 1_000_000,
                    "received_mbps": recv_delta * 8 / seconds / 1_000_000,
                    "interval_seconds": seconds,
                }
                rate["total_mbps"] = rate["sent_mbps"] + rate["received_mbps"]
                self.current_rate = rate
                if self.min_rate is None or rate["total_mbps"] < self.min_rate["total_mbps"]:
                    self.min_rate = rate
                if self.max_rate is None or rate["total_mbps"] > self.max_rate["total_mbps"]:
                    self.max_rate = rate

        self.traffic_samples.append({
            "timestamp": now,
            "sent_bytes": sent,
            "received_bytes": recv,
            "rate": rate,
        })
        self.traffic_samples = self.traffic_samples[-500:]

    def get_display_traffic_bytes(self, data):
        if data.get("firmwareMode") != "NEW":
            return (
                self.parse_int(data.get('ponBytesSent', 0)),
                self.parse_int(data.get('ponBytesReceived', 0)),
            )

        sent = 0
        recv = 0
        for i in range(1, 10):
            status = str(data.get(f'lan{i}_status', ''))
            lan_sent = self.parse_int(data.get(f'lan{i}_bytes_sent', 0))
            lan_recv = self.parse_int(data.get(f'lan{i}_bytes_received', 0))
            if status == "Up" or lan_sent > 0 or lan_recv > 0:
                sent += lan_sent
                recv += lan_recv

        for band in ("wifi24", "wifi5"):
            sent += self.parse_int(data.get(f'{band}_bytes_sent', 0))
            recv += self.parse_int(data.get(f'{band}_bytes_received', 0))

        data["interfaceBytesSentTotal"] = str(sent)
        data["interfaceBytesReceivedTotal"] = str(recv)
        return sent, recv

    def format_bytes(self, bytes_val):
        try:
            gb = bytes_val / (1024**3)
            if gb >= 1:
                return f"{gb:.2f} GB"
            mb = bytes_val / (1024**2)
            return f"{mb:.2f} MB"
        except Exception:
            return str(bytes_val)

    def format_uptime(self, seconds):
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
        except Exception:
            return str(seconds)

    def format_number(self, n):
        try:
            return f"{int(n):,}"
        except Exception:
            return str(n)

    def format_mbps(self, value):
        try:
            value = float(value)
            if value >= 1000:
                return f"{value / 1000:.2f} Gbps"
            return f"{value:.2f} Mbps"
        except (TypeError, ValueError):
            return "N/A"

    def refresh_data(self):
        self._set_status("Consultando router...", COL_ACCENT)
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        data = self.get_data()
        self.root.after(0, self._update_ui, data)

    def _update_ui(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not data:
            self._set_status("Error: No se pudo conectar", COL_RED)
            self._add("ERROR", "No se pudo conectar al router", "rojo")
            return

        if "error" in data:
            self._set_status(f"Error: {data['error'][:50]}", COL_RED)
            self._add("Error de conexion", data["error"], "rojo")
            return

        try:
            self.last_data = data
            self.last_update = datetime.now()
            self.record_traffic_sample(data)

            uptime = self.parse_int(data.get('uptime', 0))
            pon_sent, pon_recv = self.get_display_traffic_bytes(data)

            self._add_seccion("UPTIME")
            self._add("Router activo desde hace", self.format_uptime(uptime), "verde")
            self._add("Segundos totales", self.format_number(uptime), "mut")

            self._add_seccion("TRAFICO GPON")
            if data.get("firmwareMode") == "NEW":
                self._add("Estado RP3084+", "Mostrando suma LAN + WiFi 2.4 + WiFi 5", "ambar")
            self._add("Enviado", f"{self.format_bytes(pon_sent)}  ({self.format_number(pon_sent)} bytes)", "naranja")
            self._add("Recibido", f"{self.format_bytes(pon_recv)}  ({self.format_number(pon_recv)} bytes)", "verde")
            self._add("Total", self.format_bytes(pon_sent + pon_recv), "valor")

            if data.get("firmwareMode") == "NEW":
                self.insert_interface_counters(data)

            self._add_seccion("ANCHO DE BANDA EXPERIMENTAL")
            source = ("Suma LAN/WiFi del router; no WAN/GPON nativo"
                      if data.get("firmwareMode") == "NEW"
                      else "Contadores GPON del router; no trafico del PC")
            self._add("Fuente", source, "mut")
            self._add("Modo", "Calculado desde dos lecturas; no es dato nativo", "mut")
            if self.current_rate:
                self._add("Actual total", self.format_mbps(self.current_rate["total_mbps"]), "ambar")
                self._add("Actual subida", self.format_mbps(self.current_rate["sent_mbps"]), "naranja")
                self._add("Actual bajada", self.format_mbps(self.current_rate["received_mbps"]), "verde")
            else:
                self._add("Actual total", "Esperando 2 lecturas", "mut")
            self._add("Minimo sesion", self.format_mbps(self.min_rate["total_mbps"]) if self.min_rate else "N/A", "mut")
            self._add("Maximo sesion", self.format_mbps(self.max_rate["total_mbps"]) if self.max_rate else "N/A", "ambar")
            self._add("Muestras", str(len(self.traffic_samples)), "mut")

            self._add_seccion("SISTEMA")
            self._add("CPU", f"{data.get('cpu_usage', 'N/A')}%", "valor")
            mem_total = self.parse_int(data.get('mem_total', 0))
            mem_free = self.parse_int(data.get('mem_free', 0))
            mem_used = mem_total - mem_free
            mem_pct = (mem_used / mem_total * 100) if mem_total > 0 else 0
            self._add("RAM usada", f"{self.format_bytes(mem_used)}  ({mem_pct:.1f}%)", "valor")
            self._add("RAM total", self.format_bytes(mem_total), "mut")
            self._add("Modelo", data.get('ModelName', 'N/A'), "valor")
            self._add("Firmware", data.get('SoftwareVersion', 'N/A'), "valor")

            self._add_seccion("SENAL OPTICA")
            self._add("Tx Power", f"{data.get('txpower', 'N/A')} dBm", "verde")
            self._add("Rx Power", f"{data.get('rxpower', 'N/A')} dBm", "ambar")
            self._add("Temperatura", f"{data.get('transceivertemperature', 'N/A')} C", "valor")
            self._add("Voltaje", f"{data.get('supplyvottage', 'N/A')} V", "valor")
            self._add("Corriente", f"{data.get('biascurrent', 'N/A')} mA", "valor")

            self._add_seccion("WAN")
            self._add("Tipo", data.get('WANAccessType', 'N/A'), "valor")
            self._add("PON Status", data.get('pon_reg_state', 'N/A'), "valor")
            tr069 = "Activo" if data.get('tr069ipstatus') == '1' else "Inactivo"
            self._add("TR-069", tr069, "verde" if tr069 == "Activo" else "mut")

            self._set_status(f"Actualizado: {datetime.now().strftime('%H:%M:%S')}", COL_GREEN)
        except Exception as e:
            self._set_status(f"Error procesando: {e}", COL_RED)
            self._add("Error", str(e), "rojo")

    def insert_interface_counters(self, data):
        self._add_seccion("CONTADORES LAN / WIFI")
        for i in range(1, 10):
            status = str(data.get(f'lan{i}_status', ''))
            if not status:
                continue
            sent = self.parse_int(data.get(f'lan{i}_bytes_sent', 0))
            recv = self.parse_int(data.get(f'lan{i}_bytes_received', 0))
            if status != "Up" and sent == 0 and recv == 0:
                continue
            speed = data.get(f'lan{i}_speed', '')
            title = f"LAN {i}" + (f"  ({speed})" if speed else "")
            self._add("  " + title, status, "verde" if status == "Up" else "mut")
            self._add("    Enviado", f"{self.format_bytes(sent)}  ({self.format_number(sent)} bytes)", "naranja")
            self._add("    Recibido", f"{self.format_bytes(recv)}  ({self.format_number(recv)} bytes)", "verde")

        for band, label in (("wifi24", "WiFi 2.4 GHz"), ("wifi5", "WiFi 5 GHz")):
            sent = self.parse_int(data.get(f'{band}_bytes_sent', 0))
            recv = self.parse_int(data.get(f'{band}_bytes_received', 0))
            ssid = data.get(f'{band}_ssid_1', '')
            channel = data.get(f'{band}_channel', '')
            if sent == 0 and recv == 0 and not ssid and not channel:
                continue
            title = ssid or label
            suffix = f" / Canal {channel}" if channel else ""
            self._add("  " + label, f"{title}{suffix}", "valor")
            self._add("    Enviado", f"{self.format_bytes(sent)}  ({self.format_number(sent)} bytes)", "naranja")
            self._add("    Recibido", f"{self.format_bytes(recv)}  ({self.format_number(recv)} bytes)", "verde")

    def toggle_auto(self):
        if self.auto_refresh.get():
            self.auto_refresh.set(False)
            if self.auto_refresh_id:
                self.root.after_cancel(self.auto_refresh_id)
                self.auto_refresh_id = None
            self.auto_btn.config(text="Auto (60s)")
            self._set_status("Auto-refresh detenido", COL_AMBER)
        else:
            self.auto_refresh.set(True)
            self.auto_btn.config(text="Detener Auto")
            self._auto_refresh_tick()
            self._set_status("Auto-refresh activo (60s)", COL_GREEN)

    def _auto_refresh_tick(self):
        if self.auto_refresh.get():
            self.refresh_data()
            self.auto_refresh_id = self.root.after(60000, self._auto_refresh_tick)

    def clear_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.last_data = None
        self.last_update = None
        self.traffic_samples.clear()
        self.current_rate = None
        self.min_rate = None
        self.max_rate = None
        self._set_status("Datos limpiados", COL_ACCENT)

    def save_log(self):
        if not self.last_data:
            messagebox.showwarning("Sin datos", "Actualiza el router antes de exportar.")
            return

        default_name = f"router_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("Texto", "*.txt"), ("Todos", "*.*")),
            initialfile=default_name,
            title="Exportar reporte del router",
        )
        if not filename:
            return

        json_filename = os.path.splitext(filename)[0] + ".json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Monitor GPON - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"IP: {self.router_ip.get()}\n")
                f.write(f"Endpoint: {self.api_path.get()} / {self.ajax_method.get()}\n")
                if self.last_data.get("firmwareMode") == "NEW":
                    f.write("Nota: GPON muestra suma LAN + WiFi 2.4 + WiFi 5; no es WAN/GPON nativo.\n")
                else:
                    f.write("Nota: ancho de banda calculado desde contadores GPON del router; no mide trafico del PC.\n")
                f.write("=" * 60 + "\n\n")
                for item in self.tree.get_children():
                    values = self.tree.item(item, 'values')
                    if values[0] and not values[0].startswith("==="):
                        f.write(f"{values[0]}: {values[1]}\n")

            report = {
                "exported_at": datetime.now().isoformat(),
                "router": {
                    "ip": self.router_ip.get(),
                    "api_path": self.api_path.get(),
                    "ajax_method": self.ajax_method.get(),
                    "model": self.last_data.get("ModelName"),
                    "manufacturer": self.last_data.get("Manufacturer"),
                    "firmware": self.last_data.get("SoftwareVersion"),
                },
                "last_data": self.last_data,
                "bandwidth_from_router_counters": {
                    "source": ("LAN + WiFi 2.4 + WiFi 5"
                               if self.last_data.get("firmwareMode") == "NEW"
                               else "ponBytesSent/ponBytesReceived"),
                    "note": ("Suma por interfaces locales; no es WAN/GPON nativo."
                             if self.last_data.get("firmwareMode") == "NEW"
                             else "Calculado desde contadores del router entre lecturas; no mide trafico del PC."),
                    "current_mbps": self.serialize_rate(self.current_rate),
                    "min_total_mbps": self.serialize_rate(self.min_rate),
                    "max_total_mbps": self.serialize_rate(self.max_rate),
                },
                "samples": [self.serialize_sample(sample) for sample in self.traffic_samples],
            }
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Guardado", f"Reporte guardado en:\n{filename}\n{json_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def serialize_rate(self, rate):
        if not rate:
            return None
        result = dict(rate)
        result["timestamp"] = result["timestamp"].isoformat()
        return result

    def serialize_sample(self, sample):
        return {
            "timestamp": sample["timestamp"].isoformat(),
            "sent_bytes": sample["sent_bytes"],
            "received_bytes": sample["received_bytes"],
            "rate": self.serialize_rate(sample["rate"]),
        }


def main():
    root = tk.Tk()
    try:
        # Icono y centrado
        root.geometry("1000x720")
        app = RouterMonitorApp(root)
        root.mainloop()
    except tk.TclError:
        pass


if __name__ == "__main__":
    main()
