@echo off
title ScamShield - AI Inbox Immune System
echo ============================================================
echo   ScamShield - AI Inbox Immune System
echo   Starting Cognitive Defense Engine and Control Center
echo ============================================================

cd /d "%~dp0"

REM Check .env file
if not exist .env (
    if exist .env.example (
        echo [+] Generating .env from .env.example...
        copy .env.example .env >nul
    )
)

REM Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Setting up .venv...
    python -m venv .venv
    echo [+] Installing requirements...
    .venv\Scripts\pip.exe install -r requirements.txt
)

echo.
echo Active URLs:
echo   - Attack Simulator:      http://127.0.0.1:8080/simulator
echo   - OpenAPI Docs:          http://127.0.0.1:8080/docs
echo.

REM Automatically open default browser after short delay
start "" http://127.0.0.1:8080/simulator

echo [*] Launching Uvicorn server on http://127.0.0.1:8080...
echo (Press Ctrl+C to stop)
echo ------------------------------------------------------------
.venv\Scripts\python.exe -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
pause
