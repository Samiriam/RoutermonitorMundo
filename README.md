# Monitor GPON - Mundo Chile

Sistema de monitoreo para routers Huawei/FiberHome de Mundo Chile.

## Descripcion

Este proyecto permite monitorear el trafico GPON (enviado/recibido) y otros parametros del router, con el objetivo de verificar si el consumo del WiFi 5GHz esta siendo contabilizado correctamente por el ISP.

## Routers Soportados

- **Huawei HG6145F** (GPON 2.5G) - Modelo antiguo
- **Huawei HG5853SF** (XGSPON 10G) - Modelo nuevo (colegio)

Ambos routers pertenecen a Mundo Chile, mismo ISP.

## Estructura del Proyecto

```
Router_Monitor/
├── README.md                        # Este archivo
├── APK/
│   └── Monitor_GPON_v1.0.apk      # App Android (instalar en celular)
│
├── Scripts_PC/                      # Scripts para Windows
│   ├── Monitor_GPON.bat             # Menu principal (doble click)
│   ├── router_monitor_gui.py        # Interfaz grafica con tkinter
│   ├── gpon_display.py              # Consulta completa
│   ├── gpon_check.py                # Consulta rapida
│   ├── gpon_monitor.py              # Monitoreo continuo
│   ├── router_monitor_login.py      # Login con AES (firmware nuevo)
│   ├── diagnostico.py               # Diagnostico de conexion
│   ├── escanear_red.py              # Escaneo de red
│   ├── test_compatibilidad.py       # Test de firmware
│   ├── router_config.json           # Configuracion (IP, usuario, password)
│   └── polyfill_con_cryptojs.js     # Codigo JS del router (referencia)
│
├── Flutter_App/                     # Codigo fuente de la APK
│   └── router_monitor_app/
│
├── Documentacion/                   # Documentacion
│   ├── BITACORA.md                  # Bitacora detallada del proyecto
│   └── README_PARA_PROGRAMADOR.md   # Guia para el programador
│
└── Logs/                            # Registros de monitoreo
```

## Uso Rapido

### Windows (Doble click)

1. Doble click en `Monitor_GPON.bat` (en la carpeta Scripts_PC)
2. Selecciona opcion del menu:
   - **[1]** Abrir aplicacion grafica (GUI)
   - **[2]** Consulta rapida
   - **[3]** Monitoreo continuo
   - **[4]** Configurar IP/Usuario/Password
   - **[5]** Diagnostico
   - **[6]** Escanear red
   - **[7]** Salir

### Android

1. Instala `Monitor_GPON_v1.0.apk`
2. Configura la IP del router (ajustes)
3. Pull-to-refresh para actualizar

## Configuracion

Edita `Scripts_PC/router_config.json`:

```json
{
    "ip": "192.168.1.1",
    "user": "user",
    "password": "user1234"
}
```

## Datos que Obtiene

| Categoria | Informacion |
|---|---|
| **Uptime** | Tiempo desde el ultimo reinicio |
| **Trafico GPON** | Bytes enviados/recibidos (total internet) |
| **Sistema** | CPU, RAM, modelo, firmware |
| **Senal optica** | Potencia TX/RX, temperatura |
| **WAN** | Tipo de conexion, estado PON, TR-069 |

## Estado Actual

### Que funciona ✅

1. **GUI tkinter** - Interfaz grafica completa con configuracion IP/usuario/password
2. **Menu BAT** - Menu interactivo con todas las opciones
3. **APK Android** - Version 2.0 construida
4. **Auto-deteccion de firmware** - Detecta si es antiguo o nuevo
5. **Diagnostico de red** - Ping, puertos, endpoints
6. **Escaneo de red** - Busca routers en la subred

### Que NO funciona aun ❌

1. **Login AES con firmware nuevo (RP3084+)** - Implementado pero da 403
   - Causa: IP bloqueada por exceso de intentos
   - Solucion: Esperar 5-10 minutos y probar de nuevo
2. **Obtener datos especificos de WiFi 5GHz** - El router no expone estos datos por API
3. **Comparacion automatica de consumo** - Requiere login exitoso

## Comparar Consumo WiFi vs GPON

El objetivo original era comparar el consumo del WiFi 5GHz con el trafico GPON total:

1. Instala la APK en un celular conectado al WiFi 5GHz del router
2. Anota el valor de `GPON Recibido` desde la app o el script
3. Anota el consumo del WiFi 5GHz desde el celular (ajustes del sistema)
4. Compara los valores
5. Si GPON no refleja el consumo del WiFi, podria haber un bug de contabilizacion

## Para el Programador Futuro

Ver `Documentacion/BITACORA.md` y `Documentacion/README_PARA_PROGRAMADOR.md`

### Tareas pendientes

1. [ ] Implementar login AES completo y probarlo en entorno limpio
2. [ ] Obtener datos especificos de WiFi 5GHz del router
3. [ ] Crear script de comparacion automatica
4. [ ] Documentar bug si se encuentra

## Credenciales

- **Usuario**: `user`
- **Password**: `user1234`
- **IP**: `192.168.1.1`

## Tecnologias

- Python 3.x + tkinter + requests + pycryptodome
- Flutter 3.41.2 (Dart)
- Java/Kotlin (Android nativo via Flutter)
- JavaScript (CryptoJS - analizado del router)

## Repositorio

**No hay repositorio Git** conectado al proyecto.

Para crear uno:
```bash
cd C:\Users\informatica\Router_Monitor
git init
git add .
git commit -m "Initial commit: Monitor GPON Mundo Chile"
```

## Licencia

Proyecto personal de monitoreo.
