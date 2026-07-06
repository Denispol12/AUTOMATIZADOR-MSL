@echo off
chcp 65001 >nul
title MSL Validator

:: ── Verificar GEMINI_API_KEY ─────────────────────────────────────────────────
if "%GEMINI_API_KEY%"=="" (
    echo.
    echo  [ERROR] La variable de entorno GEMINI_API_KEY no esta definida.
    echo.
    echo  Para configurarla en esta sesion ejecuta:
    echo    set GEMINI_API_KEY=tu-clave-aqui
    echo.
    echo  Para configurarla permanentemente:
    echo    1. Abre "Editar las variables de entorno del sistema"
    echo    2. Agrega GEMINI_API_KEY con tu clave de https://aistudio.google.com/
    echo.
    pause
    exit /b 1
)

echo.
echo  ╔══════════════════════════════════════╗
echo  ║         MSL Validator v0.1.0         ║
echo  ╚══════════════════════════════════════╝
echo.
echo  GEMINI_API_KEY : configurada OK
echo  Servidor       : http://localhost:8000
echo.

:: ── Abrir navegador (espera 2 s para que el servidor levante) ─────────────────
ping -n 3 127.0.0.1 >nul
start "" http://localhost:8000

:: ── Iniciar uvicorn ───────────────────────────────────────────────────────────
echo  Iniciando servidor... (Ctrl+C para detener)
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
