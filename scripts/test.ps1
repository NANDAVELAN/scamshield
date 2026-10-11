$ScriptDir = Split-Path -Parent $PSScriptRoot
Set-Location $ScriptDir

& "$ScriptDir\.venv\Scripts\pytest.exe" $args
