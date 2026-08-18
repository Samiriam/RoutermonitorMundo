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
| 12 | Pasar cambios del script PC a la APK | Hecho parcial | APK `1.2.0+3` mantiene GPON real para firmware antiguo y usa WebView RP3084+ para mostrar suma LAN + WiFi 2.4 + WiFi 5 en el item GPON cuando WAN/GPON no esta expuesto. |
| 13 | Corregir GUI escritorio para RP3084+ | Hecho | `router_monitor_gui.py` ahora mantiene endpoint antiguo para firmware viejo y usa `router_web_client.js` cuando falla, mostrando suma LAN + WiFi en el item GPON para RP3084+. |
| 14 | Corregir timeout de login RP3084+ en APK Android | Pendiente de retest usuario | APK `1.2.1+4` adjunta un WebView oculto real, espera controles de login, usa eventos de input/click mas robustos y deja diagnostico si falla. |
| 15 | Corregir login APK contra router del colegio (HG5853SF) | Hecho; pendiente retest en colegio | APK `1.3.0+5` corrige payload de `DO_WEB_LOGIN` (`yhm`/`mm` en vez de `user_name`/`loginpp`), usa User-Agent de escritorio (igual al desktop que si funciona), limpia cookies antes de cada login, reintenta una vez con recarga y tolera variantes de selectores del formulario. |
| 16 | Firma estable de APK (keystore dedicado) | Hecho | Creado keystore `android/app/keystore/router_monitor.keystore` (alias `router_monitor`) y configurado `build.gradle.kts` para firmar debug y release con el mismo. Evita el error `INSTALL_FAILED_UPDATE_INCOMPATIBLE` al actualizar entre APK generadas en maquinas distintas. |
| 17 | Corregir consulta de datos APK tras login en router del trabajo (HG5853SF) | Hecho; pendiente retest en trabajo | APK `1.3.1+6`: el login WebView ya llegaba a main.html, pero la consulta `$post` fallaba por ejecutarse demasiado pronto. Se agrego espera de 2s post-login (igual que el desktop), reintento de la consulta recargando main.html sin re-loguear, y diagnostico que captura el error JS real (message/name/stack). Se preservo intacto el flujo de firmware antiguo (`get_base_info`) que funciona en casa. |
| 18 | Fix causa raiz: WebView Android no espera promesas en la consulta | Hecho; pendiente retest en trabajo | APK `1.3.2+7`: diagnosticado con navegador real (Playwright/Brave) contra el router del trabajo que `$post` y `get_device_info` SI funcionan; el fallo era que `runJavaScriptReturningResult` de Android WebView no resuelve un IIFE async (devuelve `{}`/null). Ahora el script asigna el resultado a `window.__routerMonitorResult` y Dart hace polling sincrono hasta que aparece `success`. |

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
| 2026-06-08 | `Flutter_App/router_monitor_app/lib/main.dart`, `pubspec.yaml`, `APK/Monitor_GPON_v1.2.0+3-debug.apk` | Portada logica RP3084+ a la APK con WebView: primero intenta GPON antiguo; si falla, autentica contra `login.html` y suma LAN + WiFi 2.4 + WiFi 5 en el item GPON. | `flutter pub get`, `flutter analyze`, `flutter test`, `flutter build apk --debug`. | Hecho |
| 2026-06-08 | `Scripts_PC/router_web_client.js`, `gpon_display.py`, `router_monitor_login.py`, `gpon_monitor_new.py` | Helper de escritorio ajustado para usar Brave existente en vez de descargar navegador Playwright; captura subprocess en UTF-8 para evitar fallos cp1252. | `node router_web_client.js 192.168.1.1 user user1234`, `cmd /c "echo.|python gpon_display.py 192.168.1.1"`, `cmd /c "echo.|python router_monitor_login.py"`. | Hecho |
| 2026-06-08 | `Scripts_PC/router_monitor_gui.py` | Corregida GUI de escritorio: antes solo usaba `/cgi-bin/ajax` y fallaba en RP3084+; ahora cae al helper web, muestra contadores LAN/WiFi y exporta la fuente correcta. | `python -m py_compile router_monitor_gui.py`; prueba oculta con Tk: `NEW HG5853SF RP3084` y suma LAN/WiFi calculada. | Hecho |
| 2026-06-08 | `Flutter_App/router_monitor_app/lib/main.dart`, `pubspec.yaml`, `APK/Monitor_GPON_v1.2.1+4-debug.apk` | Corregido intento de login RP3084+ en Android: el WebView ahora se monta oculto en la UI, espera controles `#user_name/#loginpp/#login_btn`, simula eventos de input/change/click y amplía diagnostico de timeout. | `flutter analyze`, `flutter test`, `flutter build apk --debug`. | Pendiente de prueba manual en celular |
| 2026-08-18 | `Flutter_App/router_monitor_app/lib/main.dart`, `pubspec.yaml`, `APK/Monitor_GPON_v1.3.0+5-debug.apk` | Fix APK contra router del colegio HG5853SF: (1) `DO_WEB_LOGIN` ahora envia `{yhm, mm}` y valida `result==0`, priorizando `window.doLoginRequest()` del propio router; (2) User-Agent del WebView cambiado de movil a escritorio Chrome 131 (el desktop que funciona en ambos routers usa navegador de escritorio); (3) se limpian cookies con `WebViewCookieManager` antes de cada login para evitar `Somebody has already logged in`; (4) se reintenta 1 vez recargando `login.html`; (5) selectores de login flexibles (`input[type=password]`, `button[type=submit]`, `.el-button--primary`) para tolerar variantes del formulario. | `flutter analyze` (sin issues), `flutter test` (paso), `flutter build apk --debug` con `JAVA_HOME=E:\jdk17-temurin`. | Pendiente retest en colegio |

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
| 2026-06-08 | El helper de escritorio dependia del Chromium descargado por Playwright y no debia instalarse Chrome/Chromium adicional en el PC. | Se elimino `C:\Users\informatica\AppData\Local\ms-playwright`; se encontro Brave instalado en `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`. | `router_web_client.js` ahora usa navegador Chromium existente o `ROUTER_MONITOR_BROWSER`. | Solucionado |
| 2026-06-08 | La GUI de escritorio mostraba `Error: No se pudo conectar` al presionar Actualizar. | Captura del usuario y revision de codigo: `router_monitor_gui.py` seguia usando solo `/cgi-bin/ajax?ajaxmethod=get_base_info`; ese endpoint falla en RP3084+. | Portar a la GUI el fallback `router_web_client.js` ya probado en scripts CLI. | Solucionado |
| 2026-06-08 | APK Android mostraba `Firmware antiguo: HTTP 403` y `timeout iniciando sesion RP3084+`. | Captura del usuario en celular; el 403 es esperado en RP3084+, pero el WebView no completaba login. Inferencia tecnica: `WebViewController` no estaba adjunto a un `WebViewWidget` visible/oculto y el click era poco robusto para Android WebView. | Montar WebView oculto 1x1, esperar controles y mejorar eventos de login. | Pendiente de retest usuario |
| 2026-08-18 | APK funcionaba con router de la casa (HG6145F RP3084+) pero no con el del colegio (HG5853SF RP3084), mientras el desktop funciona con ambos. | Evidencia de usuario + revision de codigo contra `_captured_js/login.js`: el payload de `DO_WEB_LOGIN` que enviaba la APK era `{user_name, loginpp, CSRFToken}`, pero `login.js` real usa `{yhm, mm}`; ademas el WebView usaba User-Agent movil mientras el flujo probado del desktop usa navegador de escritorio; y no se limpiaba la sesion previa del router (`Somebody has already logged in`). | Corregir payload, usar UA de escritorio, limpiar cookies antes de login, reintentar una vez y tolerar variantes de selectores. | Hecho; pendiente retest en colegio |

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
| 2026-06-08 | `node router_web_client.js 192.168.1.1 user user1234` usando Brave existente | Correcto; autentica RP3084+ y devuelve LAN, WiFi 2.4, WiFi 5 y optica sin descargar navegador Playwright. | Salida JSON en consola | Ninguno. |
| 2026-06-08 | `cmd /c "echo.|python gpon_display.py 192.168.1.1"` | Correcto; script escritorio funcional contra router actual RP3084+. | Salida de consola | Ninguno. |
| 2026-06-08 | `cmd /c "echo.|python router_monitor_login.py"` | Correcto; script login funcional contra router actual RP3084+. | Salida de consola | Ninguno. |
| 2026-06-08 | `flutter analyze` y `flutter test` | Correcto, sin issues y tests pasan. | Ninguno | Ninguno. |
| 2026-06-08 | `flutter build apk --debug` | Correcto. | `APK/Monitor_GPON_v1.2.0+3-debug.apk` de 175628309 bytes | Probar manualmente en Android contra router casa y colegio. |
| 2026-06-08 | `python -m py_compile router_monitor_gui.py` | Correcto. | Ninguno | Ninguno. |
| 2026-06-08 | Prueba oculta Tk de `RouterMonitorApp.get_data()` y `get_display_traffic_bytes()` | Correcto; devolvio `NEW HG5853SF RP3084` y suma LAN/WiFi enviada/recibida. | Salida consola | Reiniciar la GUI abierta para cargar el codigo nuevo. |
| 2026-06-08 | `flutter analyze` y `flutter test` tras fix WebView Android | Correcto, sin issues y tests pasan. | Ninguno | Ninguno. |
| 2026-06-08 | `flutter build apk --debug` tras fix WebView Android | Correcto. | `APK/Monitor_GPON_v1.2.1+4-debug.apk` de 154314914 bytes | Probar en celular contra RP3084+. |
| 2026-08-18 | `flutter analyze` tras fix colegio | Correcto, sin issues. | Ninguno | Ninguno. |
| 2026-08-18 | `flutter test` tras fix colegio | Correcto, todos los tests pasan. | Ninguno | Ninguno. |
| 2026-08-18 | `flutter build apk --debug` con `JAVA_HOME=E:\jdk17-temurin` y `ANDROID_HOME=E:\android-sdk` | Correcto. | `APK/Monitor_GPON_v1.3.0+5-debug.apk` de 154318206 bytes | Retest en celular contra router casa y colegio. |
| 2026-08-18 | Firma estable: `keytool -genkeypair` + config Gradle | Correcto; la APK queda firmada con el keystore dedicado (`CN=Router Monitor`). | `android/app/keystore/router_monitor.keystore`, `android/key.properties`, `android/app/build.gradle.kts`, `APK/Monitor_GPON_v1.3.0+5-debug.apk` (154318206 bytes) | Copiar/instalar la APK firmada y verificar que actualiza sobre la version previa. |
| 2026-08-18 | Retest usuario APK `1.3.0+5` en router del trabajo | Login llega a main.html, pero consulta falla con `fallo en login web` (error de datos vacio). | Agregar espera post-login (2s), reintento de consulta y mejor captura de error JS. | Hecho en `1.3.1+6`; pendiente retest |
| 2026-08-18 | `flutter analyze` y `flutter test` tras fix de consulta | Correcto; sin issues y tests pasan. | Ninguno | Ninguno. |
| 2026-08-18 | `flutter build apk --debug` con firma estable tras fix de consulta | Correcto. | `APK/Monitor_GPON_v1.3.1+6-debug.apk` de 154318998 bytes, misma firma (`CN=Router Monitor`) que la `1.3.0+5` | Retest en trabajo y verificar que no se rompe casa. |
| 2026-08-18 | Diagnostico con Playwright/Brave contra router del trabajo | Correcto: `$post` es function, `get_device_info` devuelve HG5853SF y todos los contadores. Prueba del script exacto de la APK via `page.evaluate`: success true con datos completos. | Ninguno | El router del trabajo NO es el problema; el fallo era el WebView Android. |
| 2026-08-18 | `flutter analyze`, `flutter test`, `flutter build apk --debug` tras fix de promesa WebView | Correcto; sin issues, tests pasan, APK compilada. | `APK/Monitor_GPON_v1.3.2+7-debug.apk` de 154319350 bytes, misma firma | Retest en trabajo. |

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
- APK `1.2.0+3` mantiene lectura GPON real para firmware antiguo y, en RP3084+, muestra en el item GPON la suma de contadores LAN + WiFi 2.4 + WiFi 5 como sustituto identificado.
- Scripts de escritorio probados funcionales contra el router actual usando Brave instalado, sin descarga local de navegador Playwright.
- GUI de escritorio corregida para RP3084+; la ventana abierta debe reiniciarse para cargar el cambio.
- APK `1.3.0+5` corrije el login WebView RP3084+ contra el router del colegio: usa payload real `DO_WEB_LOGIN` (`yhm`/`mm`), User-Agent de escritorio, limpia cookies por login y reintenta una vez con recarga de `login.html`.
- La APK ahora se firma con un keystore dedicado del proyecto (`android/app/keystore/router_monitor.keystore`), por lo que las actualizaciones futuras se instalan sobre versiones anteriores sin error de firma.
- APK `1.3.1+6` agrega espera de 2s post-login y reintento de la consulta de datos en firmware RP3084+ (router del trabajo), sin tocar el flujo de firmware antiguo que funciona en casa.
- APK `1.3.2+7` corrige la causa raiz: el WebView de Android no resuelve promesas en `runJavaScriptReturningResult`; la consulta ahora escribe en `window.__routerMonitorResult` y Dart la lee por polling. Verificado contra el router real del trabajo con navegador de escritorio que el script de consulta devuelve todos los datos.

### No Funciona / No Verificado

- Pendiente retest manual de la APK `1.3.2+7` en el router del trabajo (HG5853SF) y confirmacion de que el router de casa (HG6145F) sigue funcionando.
- No se ha probado manualmente en un celular ni contra un router real despues de los cambios.
- No hay validacion real con routers distintos al HG6145F.
- Los contadores GPON y metricas opticas del firmware RP3084+ siguen sin nodo XML confirmado; por ahora aparecen vacios o en `0`/`N/A` en el helper nuevo.
- No se encontro aun un contador total de consumo PON/WAN equivalente al `ponBytesSent/ponBytesReceived` del firmware antiguo.

### Falta Realizar

- Probar en Android: primera lectura, segunda lectura para Mbps, exportacion por WhatsApp/Drive/archivo y ajuste de endpoint.
- Si se desea compatibilidad multi-router real, crear adaptadores por fabricante/modelo con mapeo de campos y endpoints.
- Mapear en el firmware RP3084+ los nodos reales de bytes GPON y parametros opticos para completar la salida equivalente al firmware antiguo.
- Seguir buscando si existe una ruta oculta o metodo interno que exponga bytes totales PON/WAN; hasta ahora solo quedaron confirmados WiFi 5 GHz y `Optical Info`.
- Probar APK `APK\Monitor_GPON_v1.2.0+3-debug.apk` en Android contra router casa/colegio: login WebView RP3084+, primera lectura, segunda lectura para Mbps y exportacion.
- Reiniciar `Monitor_GPON.bat`/GUI y probar manualmente el boton `Actualizar` en la ventana nueva.
- Instalar y probar `APK\Monitor_GPON_v1.2.1+4-debug.apk` en Android; si falla, capturar el nuevo diagnostico que incluye `href/title/body` del WebView.
- Instalar y probar `APK\Monitor_GPON_v1.3.0+5-debug.apk` en el celular contra el router del colegio: primera lectura, segunda lectura para Mbps y exportacion. Si sigue fallando, el diagnostico ahora avisa si es `no se redirigio a main.html` (posible sesion activa de otro dispositivo) o `controles de login no encontrados` (posible pagina de login distinta).
- Instalar `APK\Monitor_GPON_v1.3.1+6-debug.apk` en el celular y probar en el router del trabajo (HG5853SF) y en el de casa (HG6145F) para confirmar que: (1) en trabajo la consulta completa de datos se entrega tras el login, (2) en casa el flujo de firmware antiguo sigue funcionando igual. Si falla la consulta, el diagnostico nuevo muestra el error JS real con `error/stack`.
