# EnergyMonitor agent — Windows install
param(
    [string]$InstallDir = "$env:ProgramFiles\EnergyMonitor\Agent",
    [string]$ModbusHost = "192.168.0.100",
    [string]$InverterProfile = "default"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

Write-Host "Installing EnergyMonitor agent to $InstallDir"

New-Item -ItemType Directory -Force -Path $InstallDir, "$InstallDir\logs", "$InstallDir\data" | Out-Null
Copy-Item -Recurse -Force "$RepoRoot\src" "$InstallDir\src"

$envContent = @"
MODBUS_HOST=$ModbusHost
MODBUS_PORT=502
INVERTER_PROFILE=$InverterProfile
SQLITE_DATABASE_PATH=data/monitor.db
LOG_FILE_PATH=logs/monitor.log
ERROR_LOG_FILE_PATH=logs/error.log
"@
Set-Content -Path "$InstallDir\.env" -Value $envContent -Encoding UTF8

python -m venv "$InstallDir\venv"
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& "$InstallDir\venv\Scripts\pip.exe" install -r "$InstallDir\src\requirements.txt" --disable-pip-version-check
$pipExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($pipExitCode -ne 0) {
    throw "pip install failed with exit code $pipExitCode"
}

$taskArgument = "`"$InstallDir\src\main.py`""
$action = New-ScheduledTaskAction -Execute "$InstallDir\venv\Scripts\python.exe" -Argument $taskArgument -WorkingDirectory $InstallDir
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "EnergyMonitorAgent" -Action $action -Trigger $trigger -RunLevel Highest -Force

Write-Host "Done. Start with: Start-ScheduledTask -TaskName EnergyMonitorAgent"
