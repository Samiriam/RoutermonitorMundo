@echo off
title Monitor GPON - Mundo Chile
color 0A
cd /d "%~dp0"

:MENU
cls
echo ============================================================
echo         MONITOR GPON - HUAWEI HG6145F (MUNDO CHILE)
echo ============================================================
echo.
echo   OPCIONES DEL MENU:
echo.
echo   [1] - Abrir Aplicacion Grafica (GUI recomendada)
echo   [2] - Consulta Rapida (una sola vez, terminal)
echo   [3] - Monitoreo Continuo (guarda log cada 1 min)
echo   [4] - Configurar IP, Usuario y Password
echo   [5] - Diagnosticar problemas de conexion
echo   [6] - Escanear red para encontrar el router
echo   [7] - Salir del programa
echo.
echo ============================================================
echo.

set /p opcion="Escriba el NUMERO de opcion (1-7) y presione ENTER: "

if "%opcion%"=="1" goto GUI
if "%opcion%"=="2" goto CONSULTA
if "%opcion%"=="3" goto CONTINUO
if "%opcion%"=="4" goto CONFIG
if "%opcion%"=="5" goto DIAGNOSTICO
if "%opcion%"=="6" goto ESCANEO
if "%opcion%"=="7" goto SALIR

echo.
echo  [!] Opcion no valida. Intente de nuevo.
timeout /t 2 >nul
goto MENU

:GUI
echo.
echo Iniciando aplicacion grafica...
echo (Cierre la ventana para volver al menu)
start /wait python router_monitor_gui.py
goto MENU

:CONSULTA
echo.
echo ============================================================
echo   CONSULTA RAPIDA
echo ============================================================
echo.
echo   Escriba la IP del router y presione ENTER
echo   o solo presione ENTER para usar 192.168.1.1
echo.
set /p router_ip="IP del Router: "
if "%router_ip%"=="" set router_ip=192.168.1.1
echo.
echo   Consultando %router_ip%...
python gpon_display.py %router_ip%
echo.
pause
goto MENU

:CONTINUO
echo.
echo ============================================================
echo   MONITOREO CONTINUO
echo ============================================================
echo.
echo   Escriba la IP del router y presione ENTER
echo   o solo presione ENTER para usar 192.168.1.1
echo.
set /p router_ip="IP del Router: "
if "%router_ip%"=="" set router_ip=192.168.1.1
echo.
echo   Monitoreando %router_ip% - Presione Ctrl+C para detener
echo.
python gpon_monitor.py %router_ip%
echo.
pause
goto MENU

:CONFIG
echo.
echo ============================================================
echo   CONFIGURAR ROUTER
echo ============================================================
echo.
echo   Abriendo archivo de configuracion...
if exist router_config.json (
    notepad router_config.json
) else (
    echo Creando configuracion por defecto...
    echo { "ip": "192.168.1.1", "user": "user", "password": "user1234" } > router_config.json
    notepad router_config.json
)
echo.
pause
goto MENU

:DIAGNOSTICO
echo.
echo ============================================================
echo   DIAGNOSTICO DE CONEXION
echo ============================================================
echo.
echo   Verificando ping, puertos, endpoints HTTP, etc.
echo.
python diagnostico.py
echo.
pause
goto MENU

:ESCANEO
echo.
echo ============================================================
echo   ESCANEO DE RED
echo ============================================================
echo.
echo   Buscando routers en la red local...
echo   Esto puede tardar 1-2 minutos.
echo.
python escanear_red.py
echo.
pause
goto MENU

:SALIR
echo.
echo   Hasta luego!
timeout /t 2 >nul
exit