#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "[*] Setting up ScamShield..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv || python -m venv .venv
fi

if [ -f ".venv/bin/pip" ]; then
    .venv/bin/pip install -r requirements.txt
elif [ -f ".venv/Scripts/pip.exe" ]; then
    .venv/Scripts/pip.exe install -r requirements.txt
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[+] Created .env template"
fi

echo "[✔] Setup complete!"
