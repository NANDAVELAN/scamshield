$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $PSScriptRoot
Set-Location $ScriptDir

Write-Host "[*] Setting up ScamShield..." -ForegroundColor Cyan
if (-not (Test-Path "$ScriptDir\.venv")) {
    python -m venv "$ScriptDir\.venv"
}

& "$ScriptDir\.venv\Scripts\pip.exe" install -r "$ScriptDir\requirements.txt"

if (-not (Test-Path "$ScriptDir\.env") -and (Test-Path "$ScriptDir\.env.example")) {
    Copy-Item "$ScriptDir\.env.example" "$ScriptDir\.env"
    Write-Host "[+] Created .env template" -ForegroundColor Yellow
}

Write-Host "[✔] Setup complete!" -ForegroundColor Green
