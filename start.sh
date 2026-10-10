#!/usr/bin/env bash
# ==============================================================================
# ScamShield — Startup Script (Linux / macOS / Git Bash / WSL)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "============================================================"
echo "🛡️  ScamShield — AI Inbox Immune System"
echo "   Starting Cognitive Defense Engine & Message Simulator"
echo "============================================================"

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[+] Creating .env from template..."
    cp .env.example .env
fi

# Detect python inside virtual environment (Windows Git Bash / MSYS vs Linux / macOS / WSL)
if [ -f ".venv/Scripts/python.exe" ]; then
    VENV_PYTHON=".venv/Scripts/python.exe"
    VENV_PIP=".venv/Scripts/pip.exe"
elif [ -f ".venv/bin/python" ]; then
    VENV_PYTHON=".venv/bin/python"
    VENV_PIP=".venv/bin/pip"
elif [ -f ".venv/Scripts/python" ]; then
    VENV_PYTHON=".venv/Scripts/python"
    VENV_PIP=".venv/Scripts/pip"
else
    VENV_PYTHON=""
    VENV_PIP=""
fi

if [ -z "$VENV_PYTHON" ]; then
    echo "[!] Creating virtual environment..."
    if command -v python3 > /dev/null 2>&1; then
        python3 -m venv .venv
    else
        python -m venv .venv
    fi
    if [ -f ".venv/Scripts/python.exe" ]; then
        VENV_PYTHON=".venv/Scripts/python.exe"
        VENV_PIP=".venv/Scripts/pip.exe"
    else
        VENV_PYTHON=".venv/bin/python"
        VENV_PIP=".venv/bin/pip"
    fi
    echo "[+] Installing dependencies from requirements.txt..."
    "$VENV_PIP" install -r requirements.txt
fi

# Check and free port 8080 if an old instance is running
if command -v cmd.exe > /dev/null 2>&1; then
    PID_8080=$(netstat -ano 2>/dev/null | grep ":8080 " | grep "LISTENING" | awk '{print $5}' | head -n 1 || true)
    if [ -n "$PID_8080" ] && [ "$PID_8080" != "0" ]; then
        echo "[!] Port 8080 is currently occupied by PID $PID_8080. Freeing port and worker tree..."
        cmd.exe /c "taskkill /F /T /PID $PID_8080" >/dev/null 2>&1 || true
        sleep 1
    fi
elif command -v lsof > /dev/null 2>&1; then
    PID_8080=$(lsof -ti:8080 || true)
    if [ -n "$PID_8080" ]; then
        echo "[!] Port 8080 is currently occupied by PID $PID_8080. Freeing port..."
        kill -9 "$PID_8080" >/dev/null 2>&1 || true
        sleep 1
    fi
fi

SIMULATOR_URL="http://127.0.0.1:8080/simulator"

echo ""
echo "Active URLs:"
echo "   - Message Simulator:        $SIMULATOR_URL"
echo "   - Phone Application (Web):  http://127.0.0.1:8080/app"
echo "   - OpenAPI Docs:             http://127.0.0.1:8080/docs"
echo ""

# Try opening default browser in background (cross-platform)
open_browser() {
    sleep 2
    if command -v cmd.exe > /dev/null 2>&1; then
        cmd.exe /c start "$SIMULATOR_URL" > /dev/null 2>&1 || true
    elif command -v powershell.exe > /dev/null 2>&1; then
        powershell.exe -NoProfile -Command "Start-Process '$SIMULATOR_URL'" > /dev/null 2>&1 || true
    elif command -v wslview > /dev/null 2>&1; then
        wslview "$SIMULATOR_URL" > /dev/null 2>&1 || true
    elif command -v xdg-open > /dev/null 2>&1; then
        xdg-open "$SIMULATOR_URL" > /dev/null 2>&1 || true
    elif command -v open > /dev/null 2>&1; then
        open "$SIMULATOR_URL" > /dev/null 2>&1 || true
    fi
}

echo "[*] Opening Message Simulator in default browser..."
open_browser &

echo "[*] Starting Uvicorn on 127.0.0.1:8080..."
echo "(Press Ctrl+C to stop)"
echo "------------------------------------------------------------"
exec "$VENV_PYTHON" -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
