# SUNHORS sunhors-agent — Windows install (Channel B)
param(
    [string]$InstallDir = "$env:ProgramFiles\Sunhors\Agent",
    [string]$ModbusHost = "192.168.0.100",
    [string]$SiteId = "demo-site",
    [string]$LicenseKey = "demo-business-key"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

Write-Host "Installing sunhors-agent to $InstallDir"

New-Item -ItemType Directory -Force -Path $InstallDir, "$InstallDir\logs", "$InstallDir\data" | Out-Null
Copy-Item -Recurse -Force "$RepoRoot\src" "$InstallDir\src"

$envContent = @"
MODBUS_HOST=$ModbusHost
MODBUS_PORT=502
SITE_ID=$SiteId
LICENSE_KEY=$LicenseKey
INVERTER_PROFILE=deye
SQLITE_DATABASE_PATH=data/sunhors.db
LICENSE_API_URL=http://localhost:8000
CLOUD_API_URL=http://localhost:8000
"@
Set-Content -Path "$InstallDir\.env" -Value $envContent -Encoding UTF8

python -m venv "$InstallDir\venv"
& "$InstallDir\venv\Scripts\pip.exe" install -r "$InstallDir\src\requirements.txt"

$action = New-ScheduledTaskAction -Execute "$InstallDir\venv\Scripts\python.exe" -Argument "$InstallDir\src\main.py" -WorkingDirectory $InstallDir
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "SunhorsAgent" -Action $action -Trigger $trigger -RunLevel Highest -Force

Write-Host "Done. Start with: Start-ScheduledTask -TaskName SunhorsAgent"
