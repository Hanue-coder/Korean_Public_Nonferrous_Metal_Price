# Run as Administrator

$taskName  = "비철금속가격_자동업데이트"
$batPath   = "C:\Choi_Sales\98_Private\Claude\update.bat"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Action
$action = New-ScheduledTaskAction -Execute $batPath

# Trigger: daily 09:00, repeat every 1 hour for 8 hours
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"
$trigger.Repetition.Interval = "PT1H"
$trigger.Repetition.Duration = "PT8H"
$trigger.Repetition.StopAtDurationEnd = $false

# Settings: run when available, no battery stop, 10 min timeout
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

# Register
Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force | Out-Null

Write-Host "등록 완료:"
schtasks /Query /TN $taskName /FO LIST 2>&1 | Select-String "Next Run|Status|Repeat"
