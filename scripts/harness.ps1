$ScriptDir = Split-Path -Parent $PSScriptRoot
Set-Location $ScriptDir

& "$ScriptDir\.venv\Scripts\python.exe" -m harness.run $args
