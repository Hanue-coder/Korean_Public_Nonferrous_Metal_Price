# Run as Administrator

$taskName = "MetalPrice_AutoUpdate"

# Remove existing task
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Action: run update.ps1
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument '-NonInteractive -ExecutionPolicy Bypass -File "C:\Choi_Sales\98_Private\Claude\update.ps1"' `
    -WorkingDirectory "C:\Choi_Sales\98_Private\Claude"

# Trigger: weekdays at 11:00 KST
$trigger = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "11:00"

# Settings: run even if the scheduled time was missed (PC was off)
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "Done: $taskName registered"
schtasks /Query /TN $taskName /FO LIST 2>&1 | Select-String "Next Run|Status|Logon Mode|Last Run"
