# Plan De Trabajo

## Plan De Trabajo

| Item | Objetivo | Estado | Evidencia / nota |
|---|---|---|---|
| 1 | Revisar estado de documentacion y app Android | Hecho | `README.md`, `Flutter_App/router_monitor_app/README.md`, `pubspec.yaml` y `lib/main.dart` revisados. |
| 2 | Confirmar fuente de medicion de trafico | Hecho | La APK usa `ponBytesSent` y `ponBytesReceived` desde `get_base_info`; no mide trafico del celular. |
| 3 | Agregar exportacion desde APK | Hecho | `lib/main.dart` agrega exportacion por `share_plus` con resumen, JSON crudo e historial de muestras. |
| 4 | Calcular maximo/minimo de ancho de banda por periodo | Hecho | Se calcula Mbps entre lecturas sucesivas del router y se guarda minimo/maximo de la sesion. |
| 5 | Investigar reutilizacion para otros routers | Hecho parcial | Confirmado HG6145F; probable en FiberHome/Huawei con API CGI similar; otros fabricantes requieren adaptador. |
| 6 | Verificar build APK | Hecho | Flutter fue localizado en `C:\Users\informatica\flutter`; APK final de prueba generada en `APK\Monitor_GPON_v1.1.0+2-debug.apk`. |
| 7 | Asegurar actualizacion Android por versionCode | Hecho | `pubspec.yaml` actualizado a `version: 1.1.0+2`; APK generada en `APK\Monitor_GPON_v1.1.0+2-debug.apk`. |
| 8 | Marcar ancho de banda como calculo experimental | Hecho | UI/documentacion ajustadas para distinguir dato calculado de dato nativo del router. |
| 9 | Verificar scripts PC contra el router actual | Hecho | Se instalo Python 3.12.10 con dependencias minimas y luego se implemento autenticacion web automatizada para RP3084+; `gpon_display.py` y `router_monitor_login.py` ya consultan datos reales del firmware nuevo sin alterar la compatibilidad del flujo antiguo. |
| 10 | Restaurar lectura de escritorio para firmware RP3084+ | Hecho parcial | El flujo nuevo inicia sesion y recupera datos reales de sistema/estado por helper web con Playwright; los contadores GPON y metricas opticas aun no tienen nodo confirmado en este firmware. |
| 11 | Buscar consumo total del router en RP3084+ | Hecho parcial | Confirmados contadores reales de `Wireless Status` 5 GHz y valores reales de `Optical Info`; los contadores PON/WAN totales siguen vacios aunque los nodos existen en el catalogo XML. |

## Cambios Realizados

| Fecha | Archivos / modulo | Cambio | Verificacion | Estado |
|---|---|---|---|---|
| 2026-06-07 | `Flutter_App/router_monitor_app/lib/main.dart` | Agregada exportacion de reporte, historial de muestras, calculo de Mbps actual/minimo/maximo y endpoint configurable. | `flutter analyze`, `flutter test`, `flutter build apk --debug`. | Hecho |
| 2026-06-07 | `Flutter_App/router_monitor_app/pubspec.yaml` | Agregada dependencia `share_plus` para compartir reportes desde Android. | `flutter pub get` con Flutter por ruta absoluta. | Hecho |
| 2026-06-07 | `README.md` | Documentado uso de exportacion, calculo de ancho de banda y compatibilidad/reutilizacion. | Lectura/edicion local. | Hecho |
| 2026-06-07 | `Flutter_App/router_monitor_app/README.md` | Reemplazada plantilla Flutter por guia tecnica de la APK. | Lectura/edicion local. | Hecho |
| 2026-06-07 | `Flutter_App/router_monitor_app/test/widget_test.dart` | Corregido smoke test generado por plantilla para usar `RouterMonitorApp`. | `flutter analyze` y `flutter test`. | Hecho |
| 2026-06-07 | `APK/Monitor_GPON_v1.1-debug.apk` | Copiada APK debug actualizada con exportacion y calculo de ancho de banda del router. | `flutter build apk --debug`. | Hecho |
| 2026-06-07 | `Flutter_App/router_monitor_app/pubspec.yaml` | Subida version real Android de `1.0.0+1` a `1.1.0+2` para permitir actualizacion sobre app instalada. | `flutter analyze`, `flutter build apk --debug`. | Hecho |
| 2026-06-07 | `APK/Monitor_GPON_v1.1.0+2-debug.apk` | Copiada APK debug con `versionCode 2`. | `flutter build apk --debug`. | Hecho |
| 2026-06-07 | `APK/Monitor_GPON_v1.1-debug.apk` | Eliminada APK intermedia obsoleta porque tenia versionado insuficiente para actualizar con claridad. | Listado final de `APK/*.apk`. | Hecho |
| 2026-06-07 | `Flutter_App/router_monitor_app/lib/main.dart` y `Scripts_PC/router_monitor_gui.py` | Cambiada la etiqueta de ancho de banda a "experimental" para no presentarlo como dato nativo. | Inspeccion de UI/documentacion. | Hecho |
| 2026-06-07 | `README.md` | Agregada lista de campos confirmados del router y nota segura sobre TR-069/compatibilidad con otras ISP. | Lectura/edicion local. | Hecho |
| 2026-06-08 | Documentacion (`PLAN_TRABAJO.md`, `Documentacion/BITACORA.md`) | Registrada verificacion del entorno actual antes de cambios de codigo y prueba bloqueada de scripts PC. | `ping 192.168.1.1`, `python --version`, `where.exe python`, `cmd /c "echo.|python gpon_display.py 192.168.1.1"`, `cmd /c "echo.|python router_monitor_login.py"`. | Hecho |
| 2026-06-08 | Entorno Windows del usuario | Instalado Python 3.12.10, agregadas rutas de Python al `PATH` de usuario e instaladas dependencias `requests` y `pycryptodome` para ejecutar los scripts PC sin tocar la logica del proyecto. | `winget install --id Python.Python.3.12 --exact --source winget --accept-source-agreements --accept-package-agreements`, verificacion por ruta absoluta y `python --version` con PATH refrescado. | Hecho |
| 2026-06-08 | `Scripts_PC/gpon_display.py`, `Scripts_PC/router_monitor_login.py`, `Scripts_PC/router_web_client.js`, `Scripts_PC/package.json`, `.gitignore` | Integrado helper web con Playwright para firmware RP3084+ usando el flujo real de `login.html`; mantiene intacto el camino antiguo `/cgi-bin/ajax` y recupera datos reales de sistema en firmware nuevo. | `node router_web_client.js 192.168.1.1 user user1234`, `python gpon_display.py 192.168.1.1`, `python router_monitor_login.py`. | Hecho |
| 2026-06-08 | `Scripts_PC/router_web_client.js`, `Scripts_PC/gpon_display.py`, `Scripts_PC/router_monitor_login.py` | Agregada extraccion de `Optical Info` y contadores `WiFi 5 GHz` desde las rutas reales del frontend (`#/status/opticalInfo/opticalInfo`, `#/status/wifiStatus/wifiStatus_5g`). | `node router_web_client.js 192.168.1.1 user user1234`, `python gpon_display.py 192.168.1.1`, `python router_monitor_login.py`. | Hecho |

## Errores, Hallazgos Y Soluciones Intentadas

| Fecha | Problema / hallazgo | Evidencia | Solucion intentada | Resultado |
|---|---|---|---|---|
| 2026-06-07 | El proyecto no es repositorio Git en `C:\Users\informatica\Router_Monitor`. | `git status --short` devolvio `fatal: not a git repository`. | Continuar sin commit y sin operaciones Git. | Funciono |
| 2026-06-07 | Flutter no esta disponible en PATH. | `flutter pub get` y `where.exe flutter` no encontraron binario. | Revisar metadatos de build y buscar SDK local. | Resuelto con ruta absoluta |
| 2026-06-07 | Flutter estaba instalado fuera de PATH. | Metadatos de build apuntaban a `C:\Users\informatica\flutter`. | Ejecutar `C:\Users\informatica\flutter\bin\flutter.bat` por ruta absoluta. | Funciono |
| 2026-06-07 | Gradle no encontraba Java. | `flutter build apk --debug` fallo con `JAVA_HOME is not set and no 'java' command could be found in your PATH`. | Buscar JDK y usar `JAVA_HOME=C:\Users\informatica\.jdks\ms-21.0.9` solo en la sesion. | Funciono |
| 2026-06-07 | Compatibilidad con otros routers no esta validada. | Documentacion confirma HG6145F y endpoints CGI; no hay pruebas con otros fabricantes. | Agregar configuracion de ruta/metodo y documentar necesidad de adaptador. | Hecho parcial |
| 2026-06-07 | Existia carpeta duplicada `C:\Users\informatica\router_monitor_app`. | La carpeta solo contenia `build/`, sin `pubspec.yaml`, `lib/` ni codigo fuente. | Eliminar carpeta generada y conservar `C:\Users\informatica\Router_Monitor` como proyecto real. | Funciono |
| 2026-06-08 | El entorno Windows no tenia Python utilizable; solo existia el alias de Microsoft Store. | `python --version` abria el alias de Store; `where.exe python` apuntaba a `WindowsApps\python.exe`; no habia `python.exe` real en `C:` ni `E:`. | Buscar instalacion existente en unidades locales y luego instalar Python 3.12.10 con `winget`, dejando el ejecutable real en `C:\Users\LASVIOLETAS-02\AppData\Local\Programs\Python\Python312\python.exe`. | Funciono |
| 2026-06-08 | `gpon_display.py` no entrega datos del router actual porque la casa ya esta en firmware nuevo RP3084+. | Ejecucion real detecto `RP3084+` y mostro mensaje de que requiere login AES. | Probar el script principal sin modificar su logica para preservar compatibilidad con el flujo antiguo. | Funciono segun lo esperado |
| 2026-06-08 | `router_monitor_login.py` sigue fallando en el login AES del firmware nuevo. | Ejecucion real obtuvo `sessionid`, genero AES y recibio `403 Forbidden` en ambos POST (`application/json` y `form data`). | Reproducir el fallo actual con el entorno Python operativo, sin tocar el codigo de escritorio ni la compatibilidad del router antiguo. | Fallo reproducido |
| 2026-06-08 | El firmware RP3084+ no usa el flujo inferido originalmente (`/fh_api/FHAPIS?ajaxmethod=do_login` con base64), sino el flujo real del navegador. | Captura con navegador automatizado: `POST /fh_api/sign/DO_WEB_LOGIN?...`, `get_device_info` y `get_value_by_xmlnode`; el login exitoso redirige a `main.html`. | Reemplazar el intento AES manual por un helper que reutiliza el flujo web autenticado del router. | Funciono |
| 2026-06-08 | Los contadores GPON/optica del firmware RP3084+ no quedaron accesibles por los nodos XML confirmados. | `get_xmlnode_js_file` expuso nodos; `get_value_by_xmlnode` devolvio datos reales para uptime/CPU/RAM/modelo/firmware/PON state, pero las rutas candidatas de bytes PON y optica devolvieron `""`. | Conservar la autenticacion funcional y documentar la limitacion mientras se siguen buscando nodos validos. | Pendiente |
| 2026-06-08 | La UI del router si muestra optica y contadores de `Wireless Status`, pero no aparecio ningun contador total PON/WAN equivalente al firmware antiguo. | Pruebas manuales del frontend con Playwright: `Optical Info` muestra TX/RX/temperatura/voltaje/corriente; `5G Wireless Status` muestra bytes/paquetes 5 GHz; `WAN Status` no muestra bytes y los nodos `Stats.Bytes*` permanecen vacios. | Extraer esos datos visibles desde la UI para mejorar el monitor y seguir dejando la busqueda de consumo total como pendiente. | Hecho parcial |

## Pruebas Y Builds

| Fecha | Comando / prueba | Resultado | Artefacto | Pendiente |
|---|---|---|---|---|
| 2026-06-07 | `flutter pub get` | Fallo: `flutter` no se reconoce como comando. | Ninguno | Instalar Flutter o agregarlo al PATH. |
| 2026-06-07 | `where.exe flutter` | No encontro binario. | Ninguno | Localizar SDK Flutter o instalarlo. |
| 2026-06-07 | `where.exe dart` | No encontro binario. | Ninguno | Localizar SDK Dart/Flutter. |
| 2026-06-07 | `C:\Users\informatica\flutter\bin\flutter.bat --version` | Flutter 3.41.2 / Dart 3.11.0. | Ninguno | Ninguno. |
| 2026-06-07 | `C:\Users\informatica\flutter\bin\flutter.bat pub get` | Correcto; resolvio `share_plus` y dependencias. | `pubspec.lock` actualizado | Ninguno. |
| 2026-06-07 | `C:\Users\informatica\flutter\bin\flutter.bat analyze` | Correcto despues de corregir `widget_test.dart`. | Ninguno | Ninguno. |
| 2026-06-07 | `C:\Users\informatica\flutter\bin\flutter.bat test` | Correcto: `All tests passed`. | Ninguno | Ninguno. |
| 2026-06-07 | `JAVA_HOME=C:\Users\informatica\.jdks\ms-21.0.9; C:\Users\informatica\flutter\bin\flutter.bat build apk --debug` | Correcto. | `Flutter_App/router_monitor_app/build/app/outputs/flutter-apk/app-debug.apk`; copia: `APK/Monitor_GPON_v1.1-debug.apk` de 185905703 bytes | Probar manualmente en Android. |
| 2026-06-07 | `Remove-Item -LiteralPath C:\Users\informatica\router_monitor_app -Recurse -Force` | Correcto; `Test-Path` posterior devolvio `False`. | Carpeta duplicada eliminada | Ninguno. |
| 2026-06-07 | `JAVA_HOME=C:\Users\informatica\.jdks\ms-21.0.9; C:\Users\informatica\flutter\bin\flutter.bat analyze` | Correcto, sin issues. | Ninguno | Ninguno. |
| 2026-06-07 | `JAVA_HOME=C:\Users\informatica\.jdks\ms-21.0.9; C:\Users\informatica\flutter\bin\flutter.bat build apk --debug` | Correcto con `versionCode 2`. | `APK/Monitor_GPON_v1.1.0+2-debug.apk` de 153647566 bytes | Probar actualizacion en Android. |
| 2026-06-07 | Listado `APK/*.apk` | Correcto. | Quedan `Monitor_GPON_v1.0.apk` y `Monitor_GPON_v1.1.0+2-debug.apk`. | Ninguno. |
| 2026-06-08 | `ping -n 2 192.168.1.1` | Correcto; el router responde en la red local. | Ninguno | Ninguno. |
| 2026-06-08 | `python --version` | Fallo; el alias de Microsoft Store indica que no hay Python funcional en PATH. | Ninguno | Instalar o localizar Python real. |
| 2026-06-08 | `where.exe python` y `py --version` | Solo existe `C:\Users\LASVIOLETAS-02\AppData\Local\Microsoft\WindowsApps\python.exe`; `py` no existe. | Ninguno | Instalar Python o ajustar PATH. |
| 2026-06-08 | `winget install --id Python.Python.3.12 --exact --source winget --accept-source-agreements --accept-package-agreements` | Correcto; Python 3.12.10 instalado. | `C:\Users\LASVIOLETAS-02\AppData\Local\Programs\Python\Python312\python.exe` | Ninguno. |
| 2026-06-08 | `C:\Users\LASVIOLETAS-02\AppData\Local\Programs\Python\Python312\python.exe -m pip install requests pycryptodome` | Correcto; dependencias minimas instaladas. | `requests 2.34.2`, `pycryptodome 3.23.0` | Ninguno. |
| 2026-06-08 | `C:\Users\LASVIOLETAS-02\AppData\Local\Programs\Python\Python312\python.exe gpon_display.py 192.168.1.1` | Correcto; detecta firmware nuevo `RP3084+` y avisa que requiere login AES. | Salida de consola | Confirmar comportamiento esperado del script principal con router de la casa actualizado. |
| 2026-06-08 | `C:\Users\LASVIOLETAS-02\AppData\Local\Programs\Python\Python312\python.exe router_monitor_login.py` | Fallo reproducido; obtiene `sessionid` pero ambos intentos de login devuelven `403 Forbidden`. | Salida de consola con `sessionid`, clave AES derivada y respuestas 403 | Investigar flujo AES exacto del firmware nuevo sin romper soporte legado. |
| 2026-06-08 | `npm.cmd install` en `Scripts_PC` | Correcto; dependencias locales del helper web instaladas (`playwright`). | `Scripts_PC/node_modules/` ignorado por Git | Ninguno. |
| 2026-06-08 | `node router_web_client.js 192.168.1.1 user user1234` | Correcto; login web automatizado y JSON real del firmware nuevo. | Salida JSON en consola | Ninguno. |
| 2026-06-08 | `python gpon_display.py 192.168.1.1` | Correcto; ahora muestra uptime/CPU/RAM/modelo/firmware y estado PON del RP3084+ mediante helper web. | Salida de consola | Pendiente mapear bytes GPON/optica reales. |
| 2026-06-08 | `python router_monitor_login.py` | Correcto; usa helper web y muestra datos del firmware nuevo en vez del `403` anterior. | Salida de consola | Pendiente mapear bytes GPON/optica reales. |
| 2026-06-08 | `node router_web_client.js 192.168.1.1 user user1234` tras extraer rutas de UI | Correcto; ahora devuelve tambien `txpower`, `rxpower`, `transceivertemperature`, `supplyvottage`, `biascurrent`, `wifi5_bytes_sent`, `wifi5_bytes_received` y SSIDs/canal 5 GHz. | Salida JSON en consola | Pendiente encontrar contadores GPON totales. |
| 2026-06-08 | `python gpon_display.py 192.168.1.1` tras extraer `Optical Info` y `5G Wireless Status` | Correcto; muestra consumo WiFi 5 GHz y senal optica reales en RP3084+. | Salida de consola | Contador GPON total sigue en `0` por falta de nodo confirmado. |

## Estado Actual

### Funciona

- App Flutter mantiene consulta principal a `get_base_info`.
- Exportacion propuesta desde APK mediante hoja de compartir Android.
- Calculo de ancho de banda observado basado en contadores del router.
- Configuracion editable de ruta API y metodo AJAX para routers compatibles.
- APK debug actualizada generada y copiada a `APK\Monitor_GPON_v1.1-debug.apk`.
- APK debug con versionCode mayor generada y copiada a `APK\Monitor_GPON_v1.1.0+2-debug.apk`.
- El ancho de banda calculado ahora se presenta como experimental/avanzado y no como campo nativo.
- El router `192.168.1.1` esta accesible por red desde este entorno.
- Python 3.12.10 ya esta instalado en el equipo con las dependencias minimas para los scripts PC.
- `gpon_display.py` mantiene el comportamiento esperado: detecta el firmware nuevo y no rompe el caso del router antiguo.
- El firmware nuevo RP3084+ ya puede autenticarse desde escritorio mediante el flujo web real del router.
- `gpon_display.py` y `router_monitor_login.py` vuelven a entregar datos reales de sistema/estado en el router de la casa actualizado.
- El helper nuevo tambien recupera potencia optica real y contadores reales de trafico WiFi 5 GHz desde la UI del router.

### No Funciona / No Verificado

- No se ha probado manualmente en un celular ni contra un router real despues de los cambios.
- No hay validacion real con routers distintos al HG6145F.
- Los contadores GPON y metricas opticas del firmware RP3084+ siguen sin nodo XML confirmado; por ahora aparecen vacios o en `0`/`N/A` en el helper nuevo.
- No se encontro aun un contador total de consumo PON/WAN equivalente al `ponBytesSent/ponBytesReceived` del firmware antiguo.

### Falta Realizar

- Probar en Android: primera lectura, segunda lectura para Mbps, exportacion por WhatsApp/Drive/archivo y ajuste de endpoint.
- Si se desea compatibilidad multi-router real, crear adaptadores por fabricante/modelo con mapeo de campos y endpoints.
- Mapear en el firmware RP3084+ los nodos reales de bytes GPON y parametros opticos para completar la salida equivalente al firmware antiguo.
- Seguir buscando si existe una ruta oculta o metodo interno que exponga bytes totales PON/WAN; hasta ahora solo quedaron confirmados WiFi 5 GHz y `Optical Info`.
