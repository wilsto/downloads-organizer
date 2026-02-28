$taskName = "DownloadsOrganizer"
$pythonExe = "C:\Users\Will\dev\Agents\Downloads\.venv\Scripts\python.exe"
$scriptPath = "C:\Users\Will\dev\Agents\Downloads\src\organizer\main.py"
$configPath = "C:\Users\Will\dev\Agents\Downloads\config.yaml"

$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "-m organizer.main --config `"$configPath`"" `
    -WorkingDirectory "C:\Users\Will\dev\Agents\Downloads"

$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 15)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Tri automatique du dossier Downloads" `
    -Force

Write-Host "Task '$taskName' registered successfully (every 15 minutes)"
