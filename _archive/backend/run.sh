#!/usr/bin/env bash
# Run ScamShield FastAPI Backend
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/.."

if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    echo "[+] Creating backend/.env from template..."
    cp backend/.env.example backend/.env
fi

if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_CMD=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo "[*] Starting ScamShield Backend on http://127.0.0.1:8000..."
"$PYTHON_CMD" -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
