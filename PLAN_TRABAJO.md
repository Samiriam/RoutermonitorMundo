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

## Errores, Hallazgos Y Soluciones Intentadas

| Fecha | Problema / hallazgo | Evidencia | Solucion intentada | Resultado |
|---|---|---|---|---|
| 2026-06-07 | El proyecto no es repositorio Git en `C:\Users\informatica\Router_Monitor`. | `git status --short` devolvio `fatal: not a git repository`. | Continuar sin commit y sin operaciones Git. | Funciono |
| 2026-06-07 | Flutter no esta disponible en PATH. | `flutter pub get` y `where.exe flutter` no encontraron binario. | Revisar metadatos de build y buscar SDK local. | Resuelto con ruta absoluta |
| 2026-06-07 | Flutter estaba instalado fuera de PATH. | Metadatos de build apuntaban a `C:\Users\informatica\flutter`. | Ejecutar `C:\Users\informatica\flutter\bin\flutter.bat` por ruta absoluta. | Funciono |
| 2026-06-07 | Gradle no encontraba Java. | `flutter build apk --debug` fallo con `JAVA_HOME is not set and no 'java' command could be found in your PATH`. | Buscar JDK y usar `JAVA_HOME=C:\Users\informatica\.jdks\ms-21.0.9` solo en la sesion. | Funciono |
| 2026-06-07 | Compatibilidad con otros routers no esta validada. | Documentacion confirma HG6145F y endpoints CGI; no hay pruebas con otros fabricantes. | Agregar configuracion de ruta/metodo y documentar necesidad de adaptador. | Hecho parcial |
| 2026-06-07 | Existia carpeta duplicada `C:\Users\informatica\router_monitor_app`. | La carpeta solo contenia `build/`, sin `pubspec.yaml`, `lib/` ni codigo fuente. | Eliminar carpeta generada y conservar `C:\Users\informatica\Router_Monitor` como proyecto real. | Funciono |

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

## Estado Actual

### Funciona

- App Flutter mantiene consulta principal a `get_base_info`.
- Exportacion propuesta desde APK mediante hoja de compartir Android.
- Calculo de ancho de banda observado basado en contadores del router.
- Configuracion editable de ruta API y metodo AJAX para routers compatibles.
- APK debug actualizada generada y copiada a `APK\Monitor_GPON_v1.1-debug.apk`.
- APK debug con versionCode mayor generada y copiada a `APK\Monitor_GPON_v1.1.0+2-debug.apk`.
- El ancho de banda calculado ahora se presenta como experimental/avanzado y no como campo nativo.

### No Funciona / No Verificado

- No se ha probado manualmente en un celular ni contra un router real despues de los cambios.
- No hay validacion real con routers distintos al HG6145F.

### Falta Realizar

- Probar en Android: primera lectura, segunda lectura para Mbps, exportacion por WhatsApp/Drive/archivo y ajuste de endpoint.
- Si se desea compatibilidad multi-router real, crear adaptadores por fabricante/modelo con mapeo de campos y endpoints.
