#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f ".venv/bin/pytest" ]; then
    .venv/bin/pytest "$@"
elif [ -f ".venv/Scripts/pytest.exe" ]; then
    .venv/Scripts/pytest.exe "$@"
else
    python -m pytest "$@"
fi
