# EnergyMonitor agent — Windows install
param(
    [string]$InstallDir = "$env:ProgramFiles\EnergyMonitor\Agent",
    [string]$ModbusHost = "192.168.0.100",
    [string]$InverterProfile = "default"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $PSScriptRoot 'functions.ps1')
$InstallDir = [System.IO.Path]::GetFullPath($InstallDir)

Write-Host "Installing EnergyMonitor agent to $InstallDir"

$envContent = @"
MODBUS_HOST=$ModbusHost
MODBUS_PORT=502
INVERTER_PROFILE=$InverterProfile
SQLITE_DATABASE_PATH=data/monitor.db
LOG_FILE_PATH=logs/monitor.log
ERROR_LOG_FILE_PATH=logs/error.log
"@
Initialize-AgentFiles -SourceRoot $RepoRoot -InstallDir $InstallDir -EnvContent $envContent

python -m venv "$InstallDir\venv"
if ($LASTEXITCODE -ne 0) {
    throw "venv creation failed with exit code $LASTEXITCODE"
}
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& "$InstallDir\venv\Scripts\pip.exe" install -r "$InstallDir\src\requirements.txt" --disable-pip-version-check
$pipExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($pipExitCode -ne 0) {
    throw "pip install failed with exit code $pipExitCode"
}

Register-AgentTask -InstallDir $InstallDir

Write-Host "Done. Start with: Start-ScheduledTask -TaskName EnergyMonitorAgent"
