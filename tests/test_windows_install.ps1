param([Parameter(Mandatory = $true)][string]$PythonExe)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\install\windows\functions.ps1')

function Assert-True($Condition, $Message) {
    if (-not $Condition) { throw $Message }
}

$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('em_install_test_' + [guid]::NewGuid().ToString('N'))
$repo = Join-Path $testRoot 'repo'
$install = Join-Path $testRoot 'Program Files\EnergyMonitor\Agent'
New-Item -ItemType Directory -Path (Join-Path $repo 'src') -Force | Out-Null
Set-Content -LiteralPath (Join-Path $repo 'src\main.py') -Value 'print("first")' -Encoding ASCII
Initialize-AgentFiles -SourceRoot $repo -InstallDir $install -EnvContent 'MODBUS_HOST=192.0.2.10'
$envPath = Join-Path $install '.env'
$envBytes = [System.IO.File]::ReadAllBytes($envPath)
Assert-True ($envBytes[0] -eq 77) 'First install must write UTF8 without BOM'
Assert-True (Test-Path -LiteralPath (Join-Path $install 'src\main.py')) 'First install must contain main.py'

$customEnv = "MODBUS_HOST=192.0.2.20`nMODBUS_DEVICE_ID=7`nMODBUS_TIMEOUT=21"
[System.IO.File]::WriteAllText($envPath, $customEnv, (New-Object System.Text.UTF8Encoding($true)))
$originalEnv = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($envPath))
Set-Content -LiteralPath (Join-Path $install 'src\obsolete.py') -Value 'old'
Set-Content -LiteralPath (Join-Path $install 'data\existing.db') -Value 'keep data'
Set-Content -LiteralPath (Join-Path $repo 'src\main.py') -Value 'print("updated")' -Encoding ASCII
Initialize-AgentFiles -SourceRoot $repo -InstallDir $install -EnvContent 'MODBUS_HOST=wrong'
Assert-True ((Get-Content -LiteralPath (Join-Path $install 'src\main.py')) -eq 'print("updated")') 'Update must replace active source'
Assert-True (-not (Test-Path -LiteralPath (Join-Path $install 'src\src'))) 'Update must not nest src'
Assert-True (-not (Test-Path -LiteralPath (Join-Path $install 'src\obsolete.py'))) 'Update must remove obsolete active source'
Assert-True ((Get-Content -LiteralPath (Join-Path $install 'data\existing.db')) -eq 'keep data') 'Update must preserve data'
Assert-True ([Convert]::ToBase64String([System.IO.File]::ReadAllBytes($envPath)) -eq $originalEnv) 'Update must preserve exact config bytes'

# Capture scheduler calls without registering or changing any Windows task.
function New-ScheduledTaskAction {
    param($Execute, $Argument, $WorkingDirectory)
    return @{ Execute=$Execute; Argument=$Argument; WorkingDirectory=$WorkingDirectory }
}
function New-ScheduledTaskTrigger { param([switch]$AtStartup) return @{ AtStartup=$AtStartup.IsPresent } }
function New-ScheduledTaskSettingsSet {
    param($RestartCount, $RestartInterval, $ExecutionTimeLimit, [switch]$StartWhenAvailable,
        [switch]$AllowStartIfOnBatteries, [switch]$DontStopIfGoingOnBatteries, $MultipleInstances)
    return $PSBoundParameters
}
function Register-ScheduledTask {
    param($TaskName, $Action, $Trigger, $Settings, $User, $RunLevel, [switch]$Force)
    $script:registeredTask = $PSBoundParameters
}
Register-AgentTask -InstallDir $install
$task = $script:registeredTask
Assert-True ($task.Action.Argument -eq ('"' + (Join-Path $install 'src\main.py') + '"')) 'Script argument must be quoted'
Assert-True ($task.Trigger.AtStartup -and $task.User -eq 'SYSTEM') 'Task must start without an interactive login'
Assert-True ($task.Settings.RestartCount -eq 999) 'Task must restart failed processes'
Assert-True ($task.Settings.ExecutionTimeLimit -eq [TimeSpan]::Zero) 'Agent must not be stopped by a task time limit'
Assert-True ($task.Settings.MultipleInstances -eq 'IgnoreNew') 'Task must prevent duplicate agents'

# Exercise the exact argument with a real Python process and a path containing spaces.
$outputPath = Join-Path $testRoot 'python-output.txt'
$process = Start-Process -FilePath $PythonExe -ArgumentList $task.Action.Argument `
    -WorkingDirectory $task.Action.WorkingDirectory -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $outputPath
Assert-True ($process.ExitCode -eq 0) 'Quoted Python launch must succeed'
Assert-True ((Get-Content -LiteralPath $outputPath) -eq 'updated') 'Python must run updated main.py'
Write-Output 'PASS: first install, upgrade, config/data preservation, task recovery settings, real quoted launch'
