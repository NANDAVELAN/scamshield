#!/usr/bin/env bash
# ==============================================================================
# ScamShield — Startup Script (Linux / macOS / WSL)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "============================================================"
echo "🛡️  ScamShield — AI Inbox Immune System"
echo "   Starting Cognitive Defense Engine and Control Center"
echo "============================================================"

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[+] Creating .env from template..."
    cp .env.example .env
fi

# Detect python inside virtual environment (Linux/macOS vs Windows Git Bash)
if [ -f ".venv/Scripts/python.exe" ]; then
    VENV_PYTHON=".venv/Scripts/python.exe"
    VENV_PIP=".venv/Scripts/pip.exe"
elif [ -f ".venv/bin/python" ]; then
    VENV_PYTHON=".venv/bin/python"
    VENV_PIP=".venv/bin/pip"
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
    "$VENV_PIP" install -r requirements.txt
fi

echo ""
echo "Active URLs:"
echo "   - Mission Control Center: http://127.0.0.1:8080/control/ui"
echo "   - Message Simulator:      http://127.0.0.1:8080/simulator"
echo "   - OpenAPI Docs:           http://127.0.0.1:8080/docs"
echo ""

# Try opening default browser
if command -v xdg-open > /dev/null; then
    (sleep 2 && xdg-open "http://127.0.0.1:8080/control/ui") &
elif command -v open > /dev/null; then
    (sleep 2 && open "http://127.0.0.1:8080/control/ui") &
fi

echo "[*] Starting Uvicorn on 127.0.0.1:8080..."
"$VENV_PYTHON" -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
