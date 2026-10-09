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

if [ ! -d ".venv" ]; then
    echo "[!] Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
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
.venv/bin/python -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
