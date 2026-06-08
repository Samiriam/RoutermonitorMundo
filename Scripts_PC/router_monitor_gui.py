#!/usr/bin/env python3
"""
Monitor GPON con Interfaz Grafica - Huawei HG6145F
Aplicacion de escritorio para Windows con configuracion de IP, usuario y password
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import threading
from datetime import datetime
import os
import json as json_lib

CONFIG_FILE = "router_config.json"

class RouterMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor GPON - Mundo Chile")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e1e")

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

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", background="#1e1e1e", foreground="white")
        self.style.configure("TFrame", background="#1e1e1e")
        self.style.configure("TButton", background="#1565C0", foreground="white")
        self.style.configure("TLabelframe", background="#1e1e1e", foreground="white")
        self.style.configure("TLabelframe.Label", background="#1e1e1e", foreground="white")
        self.style.configure("Treeview", background="#2d2d2d", foreground="white", fieldbackground="#2d2d2d")
        self.style.configure("Treeview.Heading", background="#1565C0", foreground="white")

        self.auto_refresh_id = None
        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json_lib.load(f)
            except:
                pass
        return {}

    def save_config(self):
        config = {
            "ip": self.router_ip.get(),
            "user": self.username.get(),
            "password": self.password.get(),
            "api_path": self.api_path.get(),
            "ajax_method": self.ajax_method.get()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json_lib.dump(config, f, indent=2)
            self.status_label.config(text="Configuracion guardada", foreground="#4CAF50")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            return False

    def create_widgets(self):
        # Frame de configuracion
        config_frame = ttk.LabelFrame(self.root, text="Configuracion del Router", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text="IP del Router:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(config_frame, textvariable=self.router_ip, width=20).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(config_frame, text="Usuario:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        ttk.Entry(config_frame, textvariable=self.username, width=15).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(config_frame, text="Password:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.password_entry = ttk.Entry(config_frame, textvariable=self.password, width=20, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Button(config_frame, text="Mostrar/Ocultar", command=self.toggle_password).grid(row=1, column=2, padx=5, pady=2)
        ttk.Button(config_frame, text="Guardar Config", command=self.save_config).grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(config_frame, text="Ruta API:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(config_frame, textvariable=self.api_path, width=20).grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(config_frame, text="Metodo AJAX:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        ttk.Entry(config_frame, textvariable=self.ajax_method, width=20).grid(row=2, column=3, padx=5, pady=2)

        # Frame de acciones
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(action_frame, text="Actualizar", command=self.refresh_data).pack(side="left", padx=5)
        self.auto_btn = ttk.Button(action_frame, text="Iniciar Auto (60s)", command=self.toggle_auto)
        self.auto_btn.pack(side="left", padx=5)
        ttk.Button(action_frame, text="Limpiar", command=self.clear_data).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Exportar Reporte", command=self.save_log).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Salir", command=self.root.quit).pack(side="right", padx=5)

        self.status_label = ttk.Label(action_frame, text="Listo - Configure el router y presione Actualizar", foreground="#4CAF50")
        self.status_label.pack(side="left", padx=20)

        # Frame de datos
        data_frame = ttk.LabelFrame(self.root, text="Datos del Router", padding=10)
        data_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("parametro", "valor")
        self.tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=20)
        self.tree.heading("parametro", text="Parametro")
        self.tree.heading("valor", text="Valor")
        self.tree.column("parametro", width=350, anchor="w")
        self.tree.column("valor", width=450, anchor="w")

        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def toggle_password(self):
        if self.password_entry.cget("show") == "*":
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

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
                return json.loads(resp.text)
        except Exception as e:
            return {"error": str(e)}
        return None

    def parse_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def record_traffic_sample(self, data):
        now = datetime.now()
        sent = self.parse_int(data.get('ponBytesSent', 0))
        recv = self.parse_int(data.get('ponBytesReceived', 0))
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

    def format_bytes(self, bytes_val):
        try:
            gb = bytes_val / (1024**3)
            if gb >= 1:
                return f"{gb:.2f} GB"
            mb = bytes_val / (1024**2)
            return f"{mb:.2f} MB"
        except:
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
        except:
            return str(seconds)

    def format_number(self, n):
        try:
            return f"{int(n):,}"
        except:
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
        self.status_label.config(text="Consultando router...", foreground="#2196F3")
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        data = self.get_data()
        self.root.after(0, self._update_ui, data)

    def _update_ui(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not data:
            self.status_label.config(text="Error: No se pudo conectar", foreground="#F44336")
            self.tree.insert("", "end", values=("ERROR", "No se pudo conectar al router"))
            return

        if "error" in data:
            self.status_label.config(text=f"Error: {data['error'][:50]}", foreground="#F44336")
            self.tree.insert("", "end", values=("Error de conexion", data["error"]))
            return

        try:
            self.last_data = data
            self.last_update = datetime.now()
            self.record_traffic_sample(data)

            uptime = self.parse_int(data.get('uptime', 0))
            pon_sent = self.parse_int(data.get('ponBytesSent', 0))
            pon_recv = self.parse_int(data.get('ponBytesReceived', 0))

            self.tree.insert("", "end", values=("=== UPTIME ===", ""))
            self.tree.insert("", "end", values=("  Router activo desde hace", self.format_uptime(uptime)))
            self.tree.insert("", "end", values=("  Segundos totales", self.format_number(uptime)))

            self.tree.insert("", "end", values=("=== TRAFICO GPON ===", ""))
            self.tree.insert("", "end", values=("  Enviado", f"{self.format_bytes(pon_sent)} ({self.format_number(pon_sent)} bytes)"))
            self.tree.insert("", "end", values=("  Recibido", f"{self.format_bytes(pon_recv)} ({self.format_number(pon_recv)} bytes)"))
            self.tree.insert("", "end", values=("  Total", self.format_bytes(pon_sent + pon_recv)))

            self.tree.insert("", "end", values=("=== ANCHO DE BANDA EXPERIMENTAL ===", ""))
            self.tree.insert("", "end", values=("  Fuente", "Contadores GPON del router; no trafico del PC"))
            self.tree.insert("", "end", values=("  Modo", "Calculado desde dos lecturas; no es dato nativo"))
            if self.current_rate:
                self.tree.insert("", "end", values=("  Actual total", self.format_mbps(self.current_rate["total_mbps"])))
                self.tree.insert("", "end", values=("  Actual subida", self.format_mbps(self.current_rate["sent_mbps"])))
                self.tree.insert("", "end", values=("  Actual bajada", self.format_mbps(self.current_rate["received_mbps"])))
            else:
                self.tree.insert("", "end", values=("  Actual total", "Esperando 2 lecturas"))
            self.tree.insert("", "end", values=("  Minimo sesion", self.format_mbps(self.min_rate["total_mbps"]) if self.min_rate else "N/A"))
            self.tree.insert("", "end", values=("  Maximo sesion", self.format_mbps(self.max_rate["total_mbps"]) if self.max_rate else "N/A"))
            self.tree.insert("", "end", values=("  Muestras", str(len(self.traffic_samples))))

            self.tree.insert("", "end", values=("=== SISTEMA ===", ""))
            self.tree.insert("", "end", values=("  CPU", f"{data.get('cpu_usage', 'N/A')}%"))
            mem_total = self.parse_int(data.get('mem_total', 0))
            mem_free = self.parse_int(data.get('mem_free', 0))
            mem_used = mem_total - mem_free
            mem_pct = (mem_used/mem_total*100) if mem_total > 0 else 0
            self.tree.insert("", "end", values=("  RAM usada", f"{self.format_bytes(mem_used)} ({mem_pct:.1f}%)"))
            self.tree.insert("", "end", values=("  RAM total", self.format_bytes(mem_total)))
            self.tree.insert("", "end", values=("  Modelo", data.get('ModelName', 'N/A')))
            self.tree.insert("", "end", values=("  Firmware", data.get('SoftwareVersion', 'N/A')))

            self.tree.insert("", "end", values=("=== SENAL OPTICA ===", ""))
            self.tree.insert("", "end", values=("  Tx Power", f"{data.get('txpower', 'N/A')} dBm"))
            self.tree.insert("", "end", values=("  Rx Power", f"{data.get('rxpower', 'N/A')} dBm"))
            self.tree.insert("", "end", values=("  Temperatura", f"{data.get('transceivertemperature', 'N/A')} C"))
            self.tree.insert("", "end", values=("  Voltaje", f"{data.get('supplyvottage', 'N/A')} V"))
            self.tree.insert("", "end", values=("  Corriente", f"{data.get('biascurrent', 'N/A')} mA"))

            self.tree.insert("", "end", values=("=== WAN ===", ""))
            self.tree.insert("", "end", values=("  Tipo", data.get('WANAccessType', 'N/A')))
            self.tree.insert("", "end", values=("  PON Status", data.get('pon_reg_state', 'N/A')))
            self.tree.insert("", "end", values=("  TR-069", "Activo" if data.get('tr069ipstatus') == '1' else "Inactivo"))

            self.status_label.config(text=f"Actualizado: {datetime.now().strftime('%H:%M:%S')}", foreground="#4CAF50")
        except Exception as e:
            self.status_label.config(text=f"Error procesando: {e}", foreground="#F44336")
            self.tree.insert("", "end", values=("Error", str(e)))

    def toggle_auto(self):
        if self.auto_refresh.get():
            self.auto_refresh.set(False)
            if self.auto_refresh_id:
                self.root.after_cancel(self.auto_refresh_id)
                self.auto_refresh_id = None
            self.auto_btn.config(text="Iniciar Auto (60s)")
            self.status_label.config(text="Auto-refresh detenido", foreground="#FF9800")
        else:
            self.auto_refresh.set(True)
            self.auto_btn.config(text="Detener Auto")
            self._auto_refresh_tick()
            self.status_label.config(text="Auto-refresh activo (60s)", foreground="#4CAF50")

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
        self.status_label.config(text="Datos limpiados", foreground="#2196F3")

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
                f.write("Nota: ancho de banda calculado desde contadores del router; no mide trafico del PC.\n")
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
                    "source": "ponBytesSent/ponBytesReceived",
                    "note": "Calculado desde contadores del router entre lecturas; no mide trafico del PC.",
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
    app = RouterMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
