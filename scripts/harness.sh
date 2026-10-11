#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python -m harness.run "$@"
elif [ -f ".venv/Scripts/python.exe" ]; then
    .venv/Scripts/python.exe -m harness.run "$@"
else
    python -m harness.run "$@"
fi
