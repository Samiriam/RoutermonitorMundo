# Protocolo AES del RP3084+ - Captura y Analisis

**Fecha**: 2026-06-08
**Router**: HG5853SF / RP3084+

## Flujo HTTP capturado con Playwright

El router NO expone ningun endpoint sin cifrar para datos. Todo el trafico API
pasa por AES-CBC con clave dinamica obtenida via `is_encrypt`.

### Fase 1: Inicializacion

```
GET /fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt
  Response: {"data":"<base64 AES>","enable":1,"result":1}
  -> Contiene sessionid cifrado, del cual se extrae la clave AES (primeros 16 chars)
```

### Fase 2: Login

```
GET /fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid
  Response: {"data":"<base64 AES>","enable":1,"result":1}
  -> Nuevo sessionid para la operacion

POST /fh_api/tmp/FHNCAPIS?_<random>
  Body: <hex AES encrypted payload>
  Response: {"sessionid":"<32 chars>"}
  -> Payload contiene: mod, ajaxmethod, CSRFToken, datos del login

POST /fh_api/sign/DO_WEB_LOGIN?_<random>
  Body: <hex AES encrypted payload>
  Response: {"sessionid":"<32 chars>"}
```

### Fase 3: Llamadas API (para CADA consulta)

```
GET  /fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid  -> nuevo sessionid
POST /fh_api/tmp/FHNCAPIS?_<random>  -> intercambia sessionid por token
POST /fh_api/tmp/FHAPIS?_<random>    -> payload cifrado con la consulta real
  Response: <hex AES encrypted>      -> respuesta real (datos del router)
```

### Fase 4: Ejemplo de consulta get_device_info

```
POST /fh_api/tmp/FHAPIS?_<random>
  Payload (descifrado): {"mod":"sys_diag","ajaxmethod":"get_device_info","nocheck":true}
  Response (descifrado): {area_code, port_num, devicetype, ssid_num, wifi, wifi5, ...}
```

### Fase 5: Ejemplo de consulta get_xml_childnode_value

```
POST /fh_api/tmp/FHAPIS?_<random>
  Payload (descifrado): {
    "mod":"sys_diag",
    "ajaxmethod":"get_xml_childnode_value",
    "url":"LANDevice.1.LANEthernetInterfaceConfig.",
    "num":5,
    "node":{"Status":"Status","BytesSent":"Stats.BytesSent","BytesReceived":"Stats.BytesReceived"}
  }
  Response (descifrado): {
    "data":[{"child_node_idx":1,"Status":"Up","BytesSent":"910...","BytesReceived":"120..."},...]
  }
```

## Parametros del cifrado AES

- **Algoritmo**: AES-128-CBC
- **Clave**: primeros 16 caracteres del sessionid (obtenido de `get_refresh_sessionid`)
- **IV**: caracteres ASCII 111-126 (`opqrstuvwxyz{|}~`) = 16 bytes
- **Padding**: PKCS7
- **Formato payload**: JSON string -> AES encrypt -> hex encode
- **Formato respuesta**: hex -> AES decrypt -> JSON

Extraido del JS del router (`initAesEncryptEnable`):
```javascript
var g_fhIv = "";
for (let i = 111; i <= 126; i++) { g_fhIv += String.fromCharCode(i); }
// g_fhIv = "opqrstuvwxyz{|}~"

var g_fhKey = sessionid.substring(0, 16);
```

## Por que la APK Flutter no puede conectar directamente

La funcion `$post` del JS del router gestiona todo el flujo AES automaticamente.
Replicar esto en Dart requiere:

1. Implementar AES-128-CBC con PKCS7 en Dart (factible con `encrypt` package)
2. Manejar el ciclo completo de renovacion de sessionid por cada llamada
3. Parsear las respuestas hex cifradas y extraer el JSON interno

**Complejidad**: alta. Cada consulta requiere 3 HTTP requests secuenciales
(get_refresh_sessionid -> FHNCAPIS -> FHAPIS), cada una con cifrado/descifrado AES.

## Alternativas exploradas

1. **Bridge server (Python/Node)**: Funciona, pero el usuario no quiere servidores extra.
2. **Implementar AES en Dart**: Factible pero requiere ~200 lineas de Dart + manejo
   de estado. La libreria `encrypt` de Dart soporta AES-CBC.
3. **Usar el endpoint viejo**: `/cgi-bin/ajax?ajaxmethod=get_base_info` devuelve 403
   en RP3084+. No funciona.

## Solucion actual (PC)

El script `router_web_client.js` usa Playwright (navegador headless) para hacer
el login y ejecutar `$post` en el contexto de la pagina. Esto funciona porque
Playwright tiene acceso al motor JS del navegador donde `$post` ya esta definido.

Los scripts Python (`gpon_monitor_new.py`, `gpon_display.py`) llaman a este helper
via `subprocess`. No requiere servidor extra.

## Para implementar en la APK sin bridge

Si se quiere soporte directo en Flutter, hay que portar el flujo AES a Dart:

```dart
// Pseudocodigo del flujo necesario en Dart
1. GET /fh_api/tmp/FHNCAPIS?ajaxmethod=is_encrypt
   -> extraer sessionid, clave = sessionid[0:16]
2. GET /fh_api/tmp/FHNCAPIS?ajaxmethod=get_refresh_sessionid
   -> nuevo sessionid, nueva clave
3. POST /fh_api/tmp/FHNCAPIS  (payload AES cifrado)
   -> token de sesion
4. POST /fh_api/tmp/FHAPIS     (payload AES cifrado con la consulta)
   -> respuesta AES cifrada -> descifrar -> JSON con datos

Repetir pasos 2-4 para cada consulta (device_info, LAN ports, WiFi, etc.)
```

Requiere: package `encrypt` (AES-CBC), manejo de sesiones HTTP con cookies,
y logica de reintento si la sesion expira.
