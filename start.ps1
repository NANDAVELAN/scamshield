# ==============================================================================
# ScamShield — Startup Script (Windows PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🛡️  ScamShield — AI Inbox Immune System" -ForegroundColor Cyan
Write-Host "   Starting Cognitive Defense Engine & Operator UI" -ForegroundColor DarkCyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Resolve Project Root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 2. Check and Create .env from template if missing
if (-not (Test-Path "$ScriptDir\.env")) {
    if (Test-Path "$ScriptDir\.env.example") {
        Write-Host "[+] Creating .env from .env.example template..." -ForegroundColor Yellow
        Copy-Item "$ScriptDir\.env.example" "$ScriptDir\.env"
    }
}

# 3. Virtual Environment Detection & Activation
$VenvPython = "$ScriptDir\.venv\Scripts\python.exe"
$VenvUvicorn = "$ScriptDir\.venv\Scripts\uvicorn.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Virtual environment (.venv) not found. Creating..." -ForegroundColor Yellow
    python -m venv "$ScriptDir\.venv"
    Write-Host "[+] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    & "$ScriptDir\.venv\Scripts\pip.exe" install -r "$ScriptDir\requirements.txt"
}

# 4. Check for existing process on port 8080
$ExistingProcess = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($ExistingProcess) {
    $PidToStop = $ExistingProcess.OwningProcess
    Write-Host "[!] Port 8080 is currently occupied by PID $PidToStop. Terminating old instance..." -ForegroundColor Yellow
    Stop-Process -Id $PidToStop -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host ">> Active Operator URLs:" -ForegroundColor Green
Write-Host "   - Mission Control Center: " -NoNewline -ForegroundColor White
Write-Host "http://127.0.0.1:8080/control/ui" -ForegroundColor Cyan
Write-Host "   - Message Simulator:      " -NoNewline -ForegroundColor White
Write-Host "http://127.0.0.1:8080/simulator" -ForegroundColor Cyan
Write-Host "   - Swagger OpenAPI Docs:   " -NoNewline -ForegroundColor White
Write-Host "http://127.0.0.1:8080/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "[+] Launching web browser to Control Center in 2 seconds..." -ForegroundColor DarkGray

# Launch browser asynchronously in background after 2 seconds
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:8080/control/ui"
} | Out-Null

Write-Host "[*] Starting Uvicorn backend server on 127.0.0.1:8080 (Press Ctrl+C to stop)..." -ForegroundColor Green
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

& $VenvUvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
