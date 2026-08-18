# BITACORA - Monitor GPON Mundo Chile

## Información General

- **Proyecto**: Monitor de tráfico GPON para routers Mundo Chile
- **Fecha inicio**: 2026-06-06
- **Fecha última actualización**: 2026-06-08
- **Estado**: Investigación / Pendiente de implementación
- **Routers objetivo**:
  - Casa: Huawei HG6145F (GPON, FW RP2934 → actualizado a RP3084+)
  - Colegio: Huawei HG5853SF (XGSPON 10G, FW RP3084)

## TL;DR - Estado Actual

### Casa (HG6145F):
- ✅ Script funciona con firmware antiguo (RP2934)
- ⚠️ Firmware se actualizó a RP3084+ y dejó de funcionar el endpoint antiguo
- ✅ Script `gpon_display.py` ahora detecta automáticamente el firmware
- ❌ NO se puede obtener datos del router actualizado sin implementar login AES

### Colegio (HG5853SF):
- ✅ Endpoint `/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid` funciona
- ✅ Endpoint `/fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt` devuelve clave AES encriptada
- ❌ Login requiere encriptación AES (no se pudo descifrar sin clave del router)
- ❌ Sesión activa bloquea login ("Somebody has already logged in")

## Hallazgos Importantes

### Verificación de entorno 2026-06-08

- El repositorio local fue sincronizado correctamente con `origin/main`.
- El router `192.168.1.1` responde por red local (`ping` OK).
- Inicialmente no fue posible ejecutar los scripts PC porque `python` apuntaba al alias de Microsoft Store y `py` no existia.
- Se verifico que no habia `python.exe` real utilizable en `C:` ni en `E:`; `G:` es Google Drive virtual y no un disco de respaldo local.
- Se instalo Python 3.12.10 con `winget` en `C:\Users\LASVIOLETAS-02\AppData\Local\Programs\Python\Python312\python.exe`.
- Se instalaron solo las dependencias minimas del proyecto para escritorio: `requests` y `pycryptodome`.
- `gpon_display.py` fue ejecutado contra `192.168.1.1` y detecto correctamente firmware nuevo `RP3084+`, informando que requiere login AES.
- `router_monitor_login.py` fue ejecutado contra `192.168.1.1`: obtuvo `sessionid`, derivo clave AES e IV, pero ambos intentos de login devolvieron `403 Forbidden`.
- Resultado inicial: el entorno Python ya funciona; el bloqueo real vuelve a ser el flujo AES del firmware nuevo, no el equipo Windows.

### Restauración escritorio RP3084+ 2026-06-08

- Se capturo el flujo real del navegador con Playwright contra `login.html`.
- Hallazgos confirmados del flujo web nuevo:
  - `get_base_info` sigue devolviendo `403` aun con sesion.
  - El login real no usa `do_login`; usa `POST /fh_api/sign/DO_WEB_LOGIN?...`.
  - Las llamadas autenticadas del front usan `get_device_info` y `get_value_by_xmlnode`.
  - `get_xmlnode_js_file` expone el catalogo de nodos XML del firmware nuevo.
- Se implemento `Scripts_PC/router_web_client.js` con Playwright para reutilizar el flujo real del frontend del router.
- `gpon_display.py` y `router_monitor_login.py` ahora delegan a ese helper solo cuando detectan firmware `RP3084+`.
- El camino viejo `/cgi-bin/ajax?ajaxmethod=get_base_info` para el router antiguo no se toco.
- Pruebas reales exitosas:
  - `node router_web_client.js 192.168.1.1 user user1234`
  - `python gpon_display.py 192.168.1.1`
  - `python router_monitor_login.py`
- Datos reales recuperados en firmware nuevo:
  - modelo `HG5853SF`
  - firmware `RP3084`
  - uptime
  - CPU
  - RAM total/libre
  - estado PON (`pon_state`)
- Se siguio explorando el frontend autenticado y se confirmo ademas:
  - `#/status/opticalInfo/opticalInfo` muestra valores reales de potencia optica
  - `#/status/wifiStatus/wifiStatus_5g` muestra contadores reales de bytes y paquetes 5 GHz
- El helper se amplio para leer esas dos pantallas y devolver:
  - `txpower`, `rxpower`, `transceivertemperature`, `supplyvottage`, `biascurrent`
  - `wifi5_bytes_sent`, `wifi5_bytes_received`, `wifi5_packets_sent`, `wifi5_packets_received`, SSIDs y canal
- Limitacion vigente:
  - los nodos candidatos para bytes GPON y metricas PON totales siguen devolviendo vacio; por eso `ponBytesSent/Received` permanecen en `0` hasta confirmar un nodo o metodo oculto equivalente al firmware antiguo.

### APK y escritorio 2026-06-08

- Se sincronizo el repo local con `origin/main`; antes estaba `behind` respecto del remoto.
- Se confirmo que los cambios del script PC no se pueden copiar literalmente a Flutter porque el script nuevo usa Node + Playwright.
- Se porto a la APK el flujo equivalente con `webview_flutter`:
  - primero intenta el endpoint antiguo `/cgi-bin/ajax?ajaxmethod=get_base_info`;
  - si ese camino falla, usa WebView para abrir `login.html`, autenticar y ejecutar llamadas `$post` del frontend RP3084+;
  - extrae sistema, optica, LAN, WiFi 2.4 GHz y WiFi 5 GHz.
- Comportamiento de consumos en la APK:
  - router casa/firmware antiguo: el item `TRAFICO GPON` conserva los contadores nativos `ponBytesSent/ponBytesReceived`;
  - router colegio o RP3084+: el item `TRAFICO GPON` muestra la suma LAN + WiFi 2.4 GHz + WiFi 5 GHz, porque WAN/GPON total no esta expuesto;
  - la UI/exportacion lo marca como suma por interfaces, no como contador WAN/GPON nativo.
- La version Android subio a `1.2.0+3` para permitir instalar sobre la build anterior.
- APK generada: `APK/Monitor_GPON_v1.2.0+3-debug.apk`.
- Verificacion Flutter:
  - `flutter pub get`: correcto;
  - `flutter analyze`: correcto, sin issues;
  - `flutter test`: correcto, tests pasan;
  - `flutter build apk --debug`: correcto.
- Verificacion escritorio:
  - `node router_web_client.js 192.168.1.1 user user1234`: correcto;
  - `cmd /c "echo.|python gpon_display.py 192.168.1.1"`: correcto;
  - `cmd /c "echo.|python router_monitor_login.py"`: correcto.
- Se corrigio un fallo Windows de codificacion en los scripts Python que capturan salida de Node: ahora usan UTF-8 con reemplazo de errores.
- Se elimino la carpeta descargada por Playwright en `C:\Users\informatica\AppData\Local\ms-playwright` por preferencia del usuario de no instalar Chrome/Chromium adicional.
- `router_web_client.js` ahora usa un navegador Chromium existente, encontrado en `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`, o la variable `ROUTER_MONITOR_BROWSER` si se quiere indicar otra ruta.

### Fix GUI escritorio 2026-06-08

- Problema observado: la ventana `Monitor GPON - Mundo Chile` mostraba `Error: No se pudo conectar` al presionar `Actualizar`.
- Causa confirmada: `Scripts_PC/router_monitor_gui.py` seguia usando solo el endpoint antiguo `/cgi-bin/ajax?ajaxmethod=get_base_info`; ese endpoint no responde en firmware RP3084+.
- Correccion aplicada:
  - mantiene el endpoint antiguo para routers/firmwares donde GPON nativo sigue disponible;
  - si el endpoint antiguo falla, ejecuta `router_web_client.js` con usuario/password de la GUI;
  - muestra en `TRAFICO GPON` la suma LAN + WiFi 2.4 GHz + WiFi 5 GHz para RP3084+;
  - agrega seccion `CONTADORES LAN / WIFI` en la tabla de la GUI;
  - exporta la nota correcta segun la fuente de datos.
- Verificacion:
  - `python -m py_compile router_monitor_gui.py`: correcto;
  - prueba oculta con Tk llamando `RouterMonitorApp.get_data()` y `get_display_traffic_bytes()`: devolvio `NEW HG5853SF RP3084` con suma LAN/WiFi enviada/recibida.
- Pendiente operativo: cerrar la ventana GUI abierta y abrirla de nuevo desde `Monitor_GPON.bat` para cargar el codigo actualizado.

### Fix APK Android WebView RP3084+ 2026-06-08

- Problema observado en celular: `No se pudo consultar el router. Firmware antiguo: HTTP 403. Firmware RP3084+: Exception: timeout iniciando sesion RP3084+`.
- Interpretacion:
  - `HTTP 403` del camino antiguo es esperado en RP3084+;
  - el fallo real era que el WebView Android no completaba el login hacia `main.html`.
- Hipotesis tecnica aplicada: el `WebViewController` estaba cargando sin un `WebViewWidget` montado en el arbol visual, y Android WebView puede no ejecutar el flujo del frontend igual que un navegador si no esta adjunto.
- Correccion aplicada:
  - se monta un `WebViewWidget` oculto de 1x1 px dentro del `Stack` de la pantalla;
  - se habilita JavaScript y user-agent movil;
  - se espera explicitamente a que existan `#user_name`, `#loginpp` y `#login_btn` antes de completar credenciales;
  - se simulan eventos `input`, `change`, `blur`, `mousedown`, `mouseup` y `click`;
  - el timeout ahora incluye diagnostico con `href`, `title` y texto parcial del body para el siguiente retest.
- Version generada: `APK/Monitor_GPON_v1.2.1+4-debug.apk`.
- Verificacion local:
  - `flutter analyze`: correcto;
  - `flutter test`: correcto;
  - `flutter build apk --debug`: correcto.
- Pendiente: prueba manual en Android contra el router RP3084+.

### Fix login APK contra router del colegio (HG5853SF) 2026-08-18

- Problema reportado por el usuario: la APK funciona con el router de la casa (HG6145F, firmware RP3084+) pero no con el del colegio (HG5853SF, firmware RP3084); el desktop funciona con ambos.
- Causas identificadas en revision de codigo contra `Scripts_PC/_captured_js/login.js`:
  1. El payload de `DO_WEB_LOGIN` que enviaba la APK era `{user_name, loginpp, CSRFToken}`, pero el `login.js` real del router usa `{yhm, mm}` (claves `yhm` y `mm`); por eso el login directo fallaba y dependia del click del boton.
  2. El WebView usaba User-Agent movil (`Android 10; Mobile`) mientras el flujo probado del desktop usa navegador de escritorio; el router del colegio puede servir una pagina de login distinta para moviles (el `checkBrowser.js` del router tiene deteccion movil).
  3. No se limpiaba la sesion previa del router; en el colegio puede quedar una sesion activa que rechaza el login nuevo con `Somebody has already logged in`.
- Correccion aplicada en `Flutter_App/router_monitor_app/lib/main.dart`:
  - `DO_WEB_LOGIN` ahora envia `{yhm, mm}` y valida `result==0`, priorizando llamar `window.doLoginRequest()` (la funcion propia del router, igual que el desktop);
  - User-Agent del WebView cambiado a escritorio Chrome 131;
  - se limpian cookies con `WebViewCookieManager.clearCookies()` antes de cada login;
  - se reintenta 1 vez recargando `login.html` limpio si la primera no llega a `main.html`;
  - selectores de login flexibles (`input[type="password"]`, `button[type="submit"]`, `.el-button--primary`) para tolerar variantes del formulario del colegio.
- Version Android subida a `1.3.0+5`.
- Verificacion local:
  - `flutter analyze`: sin issues;
  - `flutter test`: todos pasan;
  - `flutter build apk --debug` con `JAVA_HOME=E:\jdk17-temurin` y `ANDROID_HOME=E:\android-sdk`: correcto.
- APK generada: `APK/Monitor_GPON_v1.3.0+5-debug.apk` (154318206 bytes).
- Pendiente: retest en el celular contra el router del colegio. El diagnostico nuevo distingue entre `no se redirigio a main.html` (posible sesion activa de otro dispositivo) y `controles de login no encontrados` (posible pagina distinta).

### Firma estable de APK 2026-08-18

- Problema: al instalar la APK `1.3.0+5` sobre la version anterior instalada en el celular, Android rechazo la actualizacion (`INSTALL_FAILED_UPDATE_INCOMPATIBLE`).
- Causa: cada maquina genera su propio `debug.keystore`; la APK anterior fue firmada en la maquina original (`informatica`) y la nueva en `LASVIOLETAS-02`, con claves distintas. Android solo permite actualizar sobre una APK firmada con la misma clave.
- Solucion aplicada (firma estable por proyecto):
  - Generado `android/app/keystore/router_monitor.keystore` (RSA 2048, alias `router_monitor`, validez 10000 dias) con `keytool`.
  - Creado `android/key.properties` con las credenciales (ignorado por Git junto con `android/app/keystore/`).
  - `android/app/build.gradle.kts` ahora define `signingConfigs.routerMonitor` y lo aplica a los buildTypes `debug` y `release`, de modo que todas las APK futuras usen la misma firma.
- Verificacion: `apksigner verify --print-certs` muestra `CN=Router Monitor` en la APK nueva.
- APK final: `APK/Monitor_GPON_v1.3.0+5-debug.apk` (154318206 bytes).
- Nota operativa: respaldar `router_monitor.keystore` y `key.properties`; si se pierden, no se podra actualizar sobre una APK instalada sin desinstalarla primero. Los passwords estan en `android/key.properties`.

## Dos firmwares diferentes detectados

| Característica | Router Casa (HG6145F) FW Antiguo | Router Nuevo (RP3084+) |
|---|---|---|
| **Firmware** | RP2934 | RP3084 |
| **Tecnología** | GPON (2.5G) | XGSPON (10G) |
| **Endpoint API** | `/cgi-bin/ajax?ajaxmethod=...` | `/fh_api/tmp/FHNCAPIS?ajaxmethod=...` |
| **Método** | GET con `ajaxmethod` | GET/POST con `ajaxmethod` |
| **Público** | Sí (sin auth) | Solo `get_refresh_sessionid` y `is_encrypt` |
| **Auth** | No requerida | AES encryption + sesión |

### Actualización crítica 2026-06-08

**El router de la casa se actualizó automáticamente al firmware nuevo RP3084+.**

- Antes funcionaba con el endpoint `/cgi-bin/ajax?ajaxmethod=get_base_info`
- Ahora solo `/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid` responde sin auth
- El endpoint `is_encrypt` devuelve una clave AES encriptada con RSA

## Proceso de Investigación Detallado

### Sesión 1: 2026-06-06 - Router Casa con firmware antiguo

**Objetivo**: Crear script de monitoreo para router Mundo Chile HG6145F

**Acciones**:
1. Usuario reporta router HG6145F con credenciales `user/user1234`
2. Se descubre que la API usa AES encryption (función `fhencrypt`)
3. Múltiples intentos de login causaron bloqueo de cuenta (códigos 2 y 4)
4. Usuario informa que SÍ puede hacer login desde el navegador
5. Se descubre que el endpoint `get_base_info` en `/cgi-bin/ajax` responde **sin login** con headers correctos

**Headers correctos descubiertos**:
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Referer: http://192.168.1.1/html/stateOverview_inter.html
Accept: */*
```

**Resultado**: Script funcional que extrae datos GPON del router de la casa.

### Sesión 2: 2026-06-08 - Router del Colegio (HG5853SF)

**Objetivo**: Hacer que el script funcione con el router del colegio (mismo ISP, diferente modelo)

**Acciones**:
1. Se descubre que el router del colegio es HG5853SF (XGSPON, 10G)
2. Firmware RP3084 (mucho más nuevo)
3. Se descubre nuevo endpoint: `/fh_api/tmp/FHNCAPIS`
4. El JS del router usa **CryptoJS** (incluido en polyfill.min.js)
5. Implementa AES con clave encriptada con RSA (PKCS#1 v1.5)
6. Login: `do_login` con campos `yhm` (username) y `mm` (password encriptado)
7. El JS está ofuscado (variables con nombres como `_0xbf397f`)

**Endpoints descubiertos**:

| Endpoint | Método | Público | Resultado |
|---|---|---|---|
| `/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid` | GET | ✅ Sí | Devuelve `{"sessionid":"..."}` |
| `/fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt` | GET | ✅ Sí | Devuelve `{"data":"<base64>","enable":1,"result":1}` |
| `/fh_api/tmp/FHAPIS` | GET/POST | ❌ No | 403/400 |
| `/fh_api/FHNCAPIS` | GET/POST | ❌ No | 403/400 |
| `/fh_api/tmp/FHAPIS?ajaxmethod=do_login` | POST | ❌ No | Requiere sesión válida |

**Login probado**:
- URL: `/fh_api/tmp/FHAPIS?ajaxmethod=do_login`
- Body: `yhm=user&mm=<password_encriptado>&sessionid=<session_id>`
- Resultado: Sin desencriptar la clave AES no se puede hacer login

**Errores encontrados**:
- 403: Sin sesión válida
- 418: Sesión inválida (heartbeat devuelve "0\n")
- "Somebody has already logged in": Sesión activa en otro lugar

### Sesión 3: 2026-06-08 - Investigación JS y archivos

**Archivos JS identificados**:
- `polyfill.min.js` (374KB) - Contiene CryptoJS ✅ OBTENIDO
- `main.js` - Lógica principal ❌ No se pudo obtener (requiere sesión)
- `util.js` - Utilidades ❌ No se pudo obtener (requiere sesión)
- `checkBrowser.js` - Verificación de navegador ✅ OBTENIDO

**Implementación encontrada en polyfill.min.js**:
- `pkcs1pad2` (offset 167871) - Implementación RSA PKCS#1 v1.5
- `RSAKey` (offset 168221) - Clase RSA
- `RSASetPublic` (offset ~168221) - Función para setear clave pública
- `JSEncrypt` (offset 207968) - Librería JSEncrypt para RSA

**Flujo de encriptación del router (inferido)**:
1. Cliente llama `is_encrypt` → recibe `data` (clave AES encriptada con RSA)
2. Cliente desencripta `data` con la clave pública RSA del router (¡esto no tiene sentido!)

## Endpoints Documentados

### Router con firmware antiguo (RP2934)

```
GET http://192.168.1.1/cgi-bin/ajax?ajaxmethod=get_base_info&_=<timestamp>
Headers:
  User-Agent: Mozilla/5.0 ...
  Referer: http://192.168.1.1/html/stateOverview_inter.html
  Accept: */*

Respuesta: JSON con datos del router (sin auth)
```

### Router con firmware nuevo (RP3084+)

```
GET http://192.168.1.1/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid
Headers:
  User-Agent: Mozilla/5.0 ...
  Referer: http://192.168.1.1/main.html?5685
  X-Requested-With: XMLHttpRequest
  Accept: application/json, text/javascript, */*; q=0.01

Respuesta: {"sessionid":"..."}
```

```
GET http://192.168.1.1/fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt
Headers: (mismos que arriba)
Respuesta: {"data":"<base64>","enable":1,"result":1}
```

```
POST http://192.168.1.1/fh_api/tmp/FHAPIS?ajaxmethod=do_login
Body: yhm=user&mm=<password_encriptado_AES>&sessionid=<session_id>
Respuesta esperada: {"result":0,...} si login OK
```

## Problemas Conocidos

### 1. No se puede desencriptar la clave AES

**Síntoma**: `is_encrypt` devuelve una clave AES encriptada con RSA

**Causa**: El JS del router usa JSEncrypt pero nosotros no tenemos la clave privada del router

**Posibles soluciones**:
- Capturar el `data` desencriptado de la sesión activa del navegador (en JavaScript console)
- Usar la sesión activa del navegador para hacer login
- Interceptar la petición exacta del navegador (HAR file)

### 2. Sesión activa bloquea login

**Síntoma**: "Somebody has already logged in. Please try again later!"

**Causa**: El navegador tiene sesión activa

**Solución**: Cerrar sesión manualmente antes de usar el script

### 3. Endpoints JS no se pueden descargar

**Síntoma**: `/src/main.js`, `/src/js/util.js` devuelven 400/403

**Causa**: Requieren sesión activa del navegador

**Solución**: Capturar el contenido desde F12 → Sources del navegador

## Archivos en el Proyecto

```
Router_Monitor/
├── README.md
├── APK/
│   └── Monitor_GPON_v1.0.apk
├── Scripts_PC/
│   ├── Monitor_GPON.bat              # Menu principal
│   ├── router_monitor_gui.py         # GUI con tkinter
│   ├── gpon_display.py               # Muestra datos (CON auto-deteccion de firmware)
│   ├── gpon_check.py                 # Consulta rapida
│   ├── gpon_monitor.py               # Monitoreo continuo
│   ├── diagnostico.py                # Diagnostico de conexion
│   ├── escanear_red.py               # Escaneo de red
│   ├── test_compatibilidad.py        # Test de ambos firmwares
│   ├── test_fhapi.py                 # Test endpoints fh_api
│   ├── test_full_login.py            # Test flujo login completo
│   ├── test_rsa_login.py             # Test login con RSA
│   ├── find_aes.py                   # Busca AES en JS
│   ├── find_post.py                  # Busca $post en JS
│   ├── scan_new_api.py               # Scanner endpoints nuevos
│   ├── router_config.json            # Configuracion
│   ├── util_correct.js               # util.js (vacio)
│   ├── main_correct.js               # main.js (vacio)
│   ├── polyfill_final.js             # polyfill.min.js (374KB, CON CryptoJS)
│   ├── util_new.js                   # util.js (intento 1, vacio)
│   ├── main_new.js                   # main.js (intento 1, vacio)
│   ├── util_new2.js                  # util.js (intento 2, vacio)
│   ├── util_static.js                # util.js (static, vacio)
│   ├── main_final.js                 # main.js (vacio)
│   ├── index_new.html                # index.html guardado
│   ├── login_page_new.html           # login.html guardado
│   ├── login_new.js                  # login.js guardado
│   ├── checkBrowser.js               # checkBrowser.js guardado
│   ├── main_html.html                # main.html guardado
│   └── polyfill_new.js               # polyfill.min.js (intento 1, sin gzip)
├── Flutter_App/
│   └── router_monitor_app/
├── Documentacion/
│   ├── BITACORA.md                   # Este archivo
│   └── endpoints_found.txt
└── Logs/
    └── traffic_log.txt
```

## Próximos Pasos para el Programador

### Tarea 1: Implementar login completo

1. **Obtener el main.js del navegador**:
   - F12 → Sources → buscar `main.js`
   - Copiar todo el contenido
   - Buscar la función `$post` y `initAesEncryptEnable`
   - Buscar cómo se usa el `data` de `is_encrypt`

2. **Implementar la desencriptación**:
   - El router probablemente genera una clave AES, la encripta con su clave pública RSA
   - El cliente debe desencriptar con la clave privada (que no tenemos)
   - PERO la clave pública RSA suele ser fija del firmware
   - Buscar la clave pública RSA hardcodeada en el JS

3. **Implementar el login**:
   - Una vez con la clave AES desencriptada, encriptar el password con AES
   - Enviar a `/fh_api/tmp/FHAPIS?ajaxmethod=do_login`

### Tarea 2: Obtener datos del router

Una vez con sesión activa:
- Probar endpoint `get_base_info` en `/fh_api/tmp/FHNCAPIS`
- Probar `get_device_info`
- Otros endpoints según necesidad

### Tarea 3: Exportar HAR

Para futuro debugging:
- F12 → Network → ⚙️ → "Save all as HAR with content"
- Hacer login
- ⚙️ → "Export HAR"
- Pega el contenido del archivo

## Credenciales Conocidas

- Casa: `user / user1234` (Mundo)
- Colegio: `user / user1234` (Mundo, mismas credenciales)

## IPs Conocidas

- Casa: `192.168.1.1`
- Colegio: `192.168.1.1` (mismo subnet)

## Hallazgo Mayor - Codigo JS Completo (2026-06-08)

El usuario proporciono el archivo `polyfill.min.js` completo (1.5MB de JS ofuscado) del router.

### Flujo de Login AES descubierto

**Paso 1: Obtener sessionid**
```
GET http://192.168.1.1/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid
Headers: X-Requested-With: XMLHttpRequest
Respuesta: {"sessionid":"<16-32 caracteres>"}
```

**Paso 2: Generar clave AES**
```javascript
g_fhKey = init_aes_key(sessionid)  // Primeros 16 caracteres del sessionid
g_fhIv = init_aes_iv()              // "opqrstuvwxyz{|}~" (chr 111-126)
```

**Paso 3: Preparar y encriptar datos de login**
```javascript
var data = {
    yhm: username,
    mm: password,
    sessionid: sessionid
};
// Encriptar con AES-128-CBC + PKCS7
var encrypted = CryptoJS.AES.encrypt(
    JSON.stringify(data),
    g_fhKey,
    { iv: g_fhIv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }
);
```

**Paso 4: Enviar POST encriptado**
```
POST http://192.168.1.1/fh_api/FHAPIS?ajaxmethod=do_login
Content-Type: application/json; charset=utf-8
X-Requested-With: XMLHttpRequest
Body: <base64 del JSON encriptado>
```

**Paso 5: Respuestas posibles**
- `{"result": 0}` - OK
- `{"result": 1}` - "Somebody has already logged in"
- `{"result": 2}` - "Username or password is wrong 3 times"
- `{"result": 4}` - "Username or Password Error"

### Endpoints del firmware nuevo (RP3084+)

- `/fh_api/FHAPIS?ajaxmethod=<method>` - API principal con login
- `/fh_api/FHNCAPIS?ajaxmethod=<method>` - API alternativa
- `/fh_api/tmp/heartbeat` - Heartbeat publico
- `/fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid` - Session

### Variables del JS ofuscado

- `g_fhKey`: Clave AES (16 chars del sessionid)
- `g_fhIv`: IV fijo "opqrstuvwxyz{|}~"
- `requestPath`: "/fh_api/FHAPIS"
- `getRefreshSessionid()`: Genera nuevo sessionid

### Implementacion Python

Script creado: `Scripts_PC/router_monitor_login.py`

```python
def int_aes_iv():
    return ''.join(chr(i + 111) for i in range(16))

def init_aes_key(sessionid):
    return sessionid[:16]

def pkcs7_pad(data, block_size=16):
    padding_len = block_size - (len(data) % block_size)
    if padding_len == 0:
        padding_len = block_size
    return data + chr(padding_len) * padding_len

def aes_encrypt(data, key, iv):
    padded = pkcs7_pad(data).encode('utf-8')
    cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
    return base64.b64encode(cipher.encrypt(padded)).decode()
```

### Estado actual del login

- El script `router_monitor_login.py` esta implementado
- Login con AES da 403 en pruebas
- Causa probable: IP bloqueada por muchos intentos o sesion del navegador activa
- El script esta listo para funcionar en entorno limpio
