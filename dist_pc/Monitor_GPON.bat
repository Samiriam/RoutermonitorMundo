@echo off
chcp 65001 >nul
title Monitor GPON - Requisitos e instalacion
echo ============================================================
echo   Monitor GPON - Mundo Chile (version escritorio)
echo ============================================================
echo.
echo Este programa monitorea el trafico GPON de tu router.
echo.
echo Para el router ANTIGUO (HG6145F, casa) solo necesitas este .exe.
echo Para el router NUEVO RP3084+ (HG5853SF, colegio) ademas necesitas:
echo   - Node.js instalado  (https://nodejs.org)
echo   - Ejecutar: npm install  (descarga Playwright la primera vez)
echo.
echo ============================================================
echo   PASO 1: Abrir el programa
echo ============================================================
echo.
start "" "%~dp0Monitor_GPON.exe"
echo Programa abierto. Cierra esta ventana.
echo.
timeout /t 2 >nul
