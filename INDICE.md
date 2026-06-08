# Indice de Documentacion

Guia de navegacion para toda la documentacion del proyecto.

## Documentos Principales

| Documento | Ubicacion | Descripcion |
|---|---|---|
| **README.md** | `Router_Monitor/README.md` | Guia principal del proyecto |
| **BITACORA.md** | `Router_Monitor/Documentacion/BITACORA.md` | Bitacora detallada de todo el trabajo |
| **README_PARA_PROGRAMADOR.md** | `Router_Monitor/Documentacion/README_PARA_PROGRAMADOR.md` | Guia tecnica para continuar el desarrollo |
| **PLAN_TRABAJO.md** | `Router_Monitor/PLAN_TRABAJO.md` | Plan de trabajo del proyecto |

## Estructura del Proyecto

```
Router_Monitor/
├── README.md                          # Este nivel (guia principal)
├── INDICE.md                          # Este archivo
├── PLAN_TRABAJO.md                    # Plan de trabajo
│
├── APK/                               # Aplicacion Android
│   └── Monitor_GPON_v1.0.apk         # APK v1.0 lista para instalar
│
├── Scripts_PC/                        # Scripts para Windows
│   ├── Monitor_GPON.bat                # Menu principal (doble click)
│   ├── router_monitor_gui.py           # Interfaz grafica (tkinter)
│   ├── gpon_display.py                 # Consulta completa con auto-deteccion
│   ├── gpon_check.py                   # Consulta rapida
│   ├── gpon_monitor.py                 # Monitoreo continuo (cada 1 min)
│   ├── router_monitor_login.py         # Login AES para firmware nuevo
│   ├── diagnostico.py                  # Diagnostico de conexion
│   ├── escanear_red.py                 # Escaneo de red
│   ├── test_compatibilidad.py          # Test de firmware
│   ├── router_config.json              # Configuracion (IP, user, pass)
│   └── polyfill_con_cryptojs.js        # Codigo JS del router (referencia)
│
├── Flutter_App/                        # Codigo fuente Android
│   └── router_monitor_app/             # Proyecto Flutter
│
├── Documentacion/                      # Documentacion detallada
│   ├── BITACORA.md                     # Bitacora completa del proyecto
│   ├── README_PARA_PROGRAMADOR.md      # Guia tecnica
│   ├── endpoints_found.txt             # Endpoints descubiertos
│   └── ...
│
└── Logs/                               # Registros
```

## Como Empezar (Usuario Final)

1. **Lee**: `README.md`
2. **Ejecuta**: `Scripts_PC/Monitor_GPON.bat` (doble click)
3. **Configura**: Opcion 4 del menu (IP, usuario, password)
4. **Usa**: Opcion 1 para GUI o 2 para consulta rapida

## Como Continuar el Desarrollo (Programador)

1. **Lee primero**: `Documentacion/BITACORA.md` (estado completo del proyecto)
2. **Lee segundo**: `Documentacion/README_PARA_PROGRAMADOR.md` (proximos pasos)
3. **Revisa**: `Scripts_PC/polyfill_con_cryptojs.js` (codigo JS del router)
4. **Usa como base**: `Scripts_PC/router_monitor_login.py` (login AES)

## Archivos Clave por Tema

### Monitoreo de Trafico
- `Scripts_PC/gpon_display.py` - Muestra todos los datos del router
- `Scripts_PC/gpon_monitor.py` - Monitoreo continuo con log
- `Scripts_PC/gpon_check.py` - Consulta rapida

### Interfaz Grafica
- `Scripts_PC/router_monitor_gui.py` - GUI con tkinter
- `Scripts_PC/Monitor_GPON.bat` - Menu de opciones
- `Flutter_App/router_monitor_app/lib/main.dart` - App Android

### Login y Autenticacion
- `Scripts_PC/router_monitor_login.py` - Login AES completo
- `Scripts_PC/polyfill_con_cryptojs.js` - Codigo JS original del router

### Diagnostico
- `Scripts_PC/diagnostico.py` - Ping, puertos, endpoints
- `Scripts_PC/escanear_red.py` - Buscar routers en la red
- `Scripts_PC/test_compatibilidad.py` - Detectar version de firmware

### Configuracion
- `Scripts_PC/router_config.json` - Credenciales y IP
- `Documentacion/endpoints_found.txt` - Endpoints del router

## Historial Rapido

| Fecha | Evento |
|---|---|
| 2026-06-06 | Inicio del proyecto, descubrimiento del endpoint antiguo |
| 2026-06-08 | Descubrimiento del firmware nuevo, login AES |
| 2026-06-08 | Usuario proporciono polyfill.min.js completo |
| 2026-06-08 | Implementacion de login AES en Python |

## Tareas Pendientes

Ver `PLAN_TRABAJO.md` y `Documentacion/BITACORA.md` seccion "Proximos Pasos"

## Estado del Repositorio

**No hay repositorio Git** conectado. Para crear uno:

```bash
cd C:\Users\informatica\Router_Monitor
git init
git add .
git commit -m "Initial commit: Monitor GPON Mundo Chile v1.0"
```
