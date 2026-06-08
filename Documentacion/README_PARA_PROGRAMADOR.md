# README para el Programador - Monitor GPON Mundo Chile

## Estado del Proyecto

El proyecto consiste en monitorear routers Huawei de Mundo Chile (Chile). Hay dos routers objetivo:
- **Casa**: Huawei HG6145F (era GPON FW RP2934, ahora actualizado a RP3084+)
- **Colegio**: Huawei HG5853SF (XGSPON 10G, FW RP3084)

## Lo que funciona ✅

1. **Detección automática de firmware** en `gpon_display.py` y `test_compatibilidad.py`
2. **Interfaz gráfica** (`router_monitor_gui.py`) con configuración de IP, usuario, password
3. **Menú BAT** con opciones de GUI, consulta, monitoreo, configuración, diagnóstico
4. **Scripts de diagnóstico** (`diagnostico.py`, `escanear_red.py`, `test_compatibilidad.py`)
5. **APK Android** (v1.0) con UI básica

## Lo que NO funciona ❌

1. **Obtener datos del router con firmware nuevo (RP3084+)** - requiere login con encriptación AES
2. **Script de login con RSA** (`test_rsa_login.py`) - falla porque el "data" de `is_encrypt` no es una clave pública RSA estándar, sino una clave AES encriptada con RSA

## El Problema Técnico Detallado

### Endpoint `is_encrypt` devuelve:
```json
{
  "data": "aas0j8FEsGJDnmQFWN3Rq0MmVyJM4Lz4yGUkAqixg2fjx8cVAa1z3qYtk0qa04YNNx1uzDKce+nR+lXlldNN5TNAi0PhpO/DFSJJx23xrUIJgOeqW5HNT3+6TodN80grxgXAb8qesJXP/yCCKHKuCJAF1J9S7istjF8MIlIfG97/veH2QDIx4qm3AvrT9Yvtzr0cNwpYzyw5IVAY1enkcYhFOLphheJ5VfIoOn6b3PMA3L6ivTbQCa1nsz03oeH6/IoVnQLL2yCNcuqpYrsKTrhzFBwMwUosNLOD5ShlHw1n9Syswdx3tqQCuhQGPDJIDu3fypCmyDlKoD9QE/8PZg==",
  "enable": 1,
  "result": 1
}
```

El `data` es base64 que al decodificar son **256 bytes binarios** (no es PEM, no es X.509, no es PKCS#1 estándar).

### Flujo de encriptación del router (INFERIDO, no confirmado):

1. El router genera una clave AES aleatoria de 16/32 bytes
2. La encripta con su clave pública RSA
3. Te la envía codificada en base64
4. El cliente la desencripta con la clave privada RSA (que el JS debe tener hardcodeada)
5. Usa la clave AES para encriptar el password
6. Envía el password encriptado con AES al endpoint de login

### Lo que falta:

La **clave privada RSA** del router o el **método exacto** para desencriptar el `data` de `is_encrypt`.

## Archivos Clave para Continuar

### Scripts Python (en `Scripts_PC/`):

| Archivo | Estado | Descripción |
|---|---|---|
| `gpon_display.py` | ✅ Funciona con FW antiguo | Muestra datos con auto-detección |
| `gpon_check.py` | ⚠️ Usa FW antiguo | Consulta rápida |
| `gpon_monitor.py` | ⚠️ Usa FW antiguo | Monitoreo continuo |
| `router_monitor_gui.py` | ✅ Funciona | GUI con tkinter |
| `test_rsa_login.py` | ❌ Falla | Intento de login con RSA |
| `test_fhapi.py` | ✅ Útil | Test endpoints fh_api |
| `test_full_login.py` | ❌ Falla | Test flujo login completo |
| `scan_new_api.py` | ✅ Útil | Scanner endpoints |
| `test_compatibilidad.py` | ✅ Funciona | Detecta firmware |
| `polyfill_con_cryptojs.js` | ✅ IMPORTANTE | polyfill.min.js del router con CryptoJS |

### Documentación:

- `Documentacion/BITACORA.md` - Bitácora completa del proyecto
- `Documentacion/endpoints_found.txt` - Endpoints descubiertos

## Cómo Continuar el Trabajo

### Paso 1: Obtener el `main.js` del router

El navegador carga `main.js` que contiene la lógica de encriptación. No se puede descargar directamente porque requiere sesión.

**Método 1: HAR file**
1. F12 → Network → ⚙️ → "Save all as HAR with content"
2. Login normal
3. ⚙️ → "Export HAR"
4. Buscar en el HAR la respuesta a `main.js`

**Método 2: Sources panel**
1. F12 → Sources
2. Navegar a `main.js`
3. Ctrl+A → Ctrl+C → pegar en un archivo
4. Especialmente buscar:
   - `initAesEncryptEnable` (offset 333249 en polyfill)
   - `do_login` y cómo se invoca
   - El uso de `is_encrypt` data

### Paso 2: Analizar la encriptación

Una vez con `main.js`, buscar:
- Cómo se usa el `data` de `is_encrypt`
- Dónde está la clave RSA privada o pública
- El método de padding (probablemente PKCS#1 v1.5 por `pkcs1pad2`)
- El modo AES (probablemente CBC o ECB)
- El IV (puede ser fijo o derivado)

### Paso 3: Implementar el login

Basado en el análisis de `main.js`, actualizar `test_rsa_login.py` o crear un nuevo script que:
1. Obtenga sessionid
2. Obtenga clave pública AES (vía `is_encrypt`)
3. Desencriptar la clave AES (con método encontrado en main.js)
4. Encriptar el password con AES
5. Hacer POST a `/fh_api/tmp/FHAPIS?ajaxmethod=do_login` con `yhm`, `mm` (encriptado), `sessionid`

### Paso 4: Obtener datos

Una vez logueado, probar:
- `/fh_api/tmp/FHNCAPIS?ajaxmethod=get_base_info`
- `/fh_api/tmp/FHNCAPIS?ajaxmethod=get_device_info`
- `/fh_api/tmp/FHNCAPIS?ajaxmethod=get_wifi_info`
- Y todos los que sean necesarios

## Información Técnica Recolectada

### Headers correctos para el firmware nuevo:
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Referer: http://192.168.1.1/main.html?5685
X-Requested-With: XMLHttpRequest
Accept: application/json, text/javascript, */*; q=0.01
```

### Endpoints públicos (sin auth):
- `GET /fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid` → `{"sessionid":"..."}`
- `GET /fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt` → `{"data":"<base64>","enable":1,"result":1}`

### Endpoint de login (requiere auth):
- `POST /fh_api/tmp/FHAPIS?ajaxmethod=do_login`
- Body: `yhm=<user>&mm=<password_encriptado>&sessionid=<session_id>`

### Endpoints que NO existen en el nuevo firmware:
- `/cgi-bin/ajax?ajaxmethod=get_base_info` (devuelve HTML 400)

## Recomendación Final

Si el programador futuro no puede obtener el `main.js`, la alternativa es:

1. **Usar un proxy MITM** entre el navegador y el router
2. **Modificar el firmware** del router para añadir un endpoint de datos sin auth (avanzado, riesgoso)
3. **Pedir al ISP que abra los datos** (improbable)
4. **Capturar tráfico con Wireshark** mientras navegas el panel del router y analizar las tramas

La opción más viable es **capturar el HAR** con todas las respuestas, o **copiar el main.js** desde F12 → Sources.

## Archivos a No Eliminar

Estos archivos son **críticos** para continuar el trabajo:
- `polyfill_con_cryptojs.js` (374KB) - Contiene la implementación de CryptoJS
- `BITACORA.md` - Documentación completa
- `README_PARA_PROGRAMADOR.md` - Este archivo
- `gpon_display.py` - Funciona con firmware antiguo (referencia)
- `test_fhapi.py` - Test de endpoints

## Contacto

Si tienes preguntas sobre el proyecto, contacta al usuario que inició este chat. La intención original era monitorear el consumo de WiFi 5GHz para verificar si el ISP estaba contabilizando bien el tráfico.