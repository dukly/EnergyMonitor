# Shared installation steps, also exercised without registering a system task.
function Initialize-AgentFiles {
    param(
        [Parameter(Mandatory = $true)][string]$SourceRoot,
        [Parameter(Mandatory = $true)][string]$InstallDir,
        [Parameter(Mandatory = $true)][string]$EnvContent
    )

    $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot 'src'))
    $installPath = [System.IO.Path]::GetFullPath($InstallDir)
    $targetPath = Join-Path $installPath 'src'
    if ($sourcePath.TrimEnd('\') -eq $targetPath.TrimEnd('\')) {
        throw 'InstallDir must differ from the source repository.'
    }
    if ($installPath.StartsWith($sourcePath.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'InstallDir must not be inside the source directory.'
    }
    if ($sourcePath.StartsWith($targetPath.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'The destination source directory must not contain the source repository.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $sourcePath 'main.py') -PathType Leaf)) {
        throw 'Source main.py is missing.'
    }
    New-Item -ItemType Directory -Force -Path $installPath,
        (Join-Path $installPath 'logs'), (Join-Path $installPath 'data') | Out-Null

    # Replace the source tree as a unit. Keep the previous version for rollback.
    $stagePath = Join-Path $installPath ('.src-stage-' + [guid]::NewGuid().ToString('N'))
    Copy-Item -LiteralPath $sourcePath -Destination $stagePath -Recurse -Force
    $backupPath = $null
    if (Test-Path -LiteralPath $targetPath) {
        if ((Get-Item -LiteralPath $targetPath -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            throw 'Refusing to replace a source directory that is a link.'
        }
        $backupPath = Join-Path $installPath ('.src-backup-' + [guid]::NewGuid().ToString('N'))
        Move-Item -LiteralPath $targetPath -Destination $backupPath
    }
    try {
        Move-Item -LiteralPath $stagePath -Destination $targetPath
    }
    catch {
        if ($backupPath -and -not (Test-Path -LiteralPath $targetPath)) {
            Move-Item -LiteralPath $backupPath -Destination $targetPath
        }
        throw
    }

    $envPath = Join-Path $installPath '.env'
    if (-not (Test-Path -LiteralPath $envPath)) {
        [System.IO.File]::WriteAllText($envPath, $EnvContent, (New-Object System.Text.UTF8Encoding($false)))
    }
}

function Register-AgentTask {
    param([Parameter(Mandatory = $true)][string]$InstallDir)

    $action = New-ScheduledTaskAction -Execute (Join-Path $InstallDir 'venv\Scripts\python.exe') `
        -Argument ('"' + (Join-Path $InstallDir 'src\main.py') + '"') -WorkingDirectory $InstallDir
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $taskSettings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName 'EnergyMonitorAgent' -Action $action -Trigger $trigger `
        -Settings $taskSettings -User 'SYSTEM' -RunLevel Highest -Force | Out-Null
}
