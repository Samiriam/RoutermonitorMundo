# Monitor GPON Android

APK Flutter para consultar valores del router GPON desde la red local. La app no mide el trafico del celular; lee contadores y estado publicados por el router.

Version Android actual: `1.1.0+2` (`versionName 1.1.0`, `versionCode 2`).

## Funciones

- Consulta `get_base_info` en `/cgi-bin/ajax` por HTTP.
- Muestra uptime, trafico acumulado GPON, CPU, RAM, modelo, firmware, senal optica y estado WAN.
- Calcula ancho de banda observado en Mbps comparando `ponBytesSent` y `ponBytesReceived` entre refrescos.
- Mantiene maximo y minimo de la sesion abierta.
- Exporta reporte por la hoja de compartir de Android con resumen, JSON crudo e historial de muestras.
- Permite configurar IP, usuario, password, ruta API y metodo AJAX.

## Reutilizacion En Otros Routers

Compatibilidad confirmada: Huawei/FiberHome HG6145F con API `get_base_info`.

Compatibilidad probable: routers FiberHome/Huawei con CGI similar y campos equivalentes.

Para routers de otros fabricantes se requiere validar endpoints y adaptar nombres de campos. La configuracion de ruta/metodo ayuda cuando el contrato JSON mantiene los mismos campos, pero no reemplaza un adaptador para APIs distintas.

## Verificacion Local

Comandos esperados cuando Flutter este disponible en PATH:

```powershell
flutter pub get
flutter analyze
flutter build apk --debug
```
