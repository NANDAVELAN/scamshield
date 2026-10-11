#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f ".venv/bin/uvicorn" ]; then
    .venv/bin/uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
elif [ -f ".venv/Scripts/uvicorn.exe" ]; then
    .venv/Scripts/uvicorn.exe server.main:app --host 127.0.0.1 --port 8080 --reload
else
    python -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
fi
