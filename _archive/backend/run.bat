@echo off
REM Run ScamShield FastAPI Backend on Windows
cd /d "%~dp0\.."

if not exist "backend\.env" if exist "backend\.env.example" (
    echo [+] Creating backend\.env from template...
    copy "backend\.env.example" "backend\.env" >nul
)

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo [*] Starting ScamShield Backend on http://127.0.0.1:8000...
"%PYTHON_CMD%" -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
