# Run as Administrator

$taskName = "MetalPrice_AutoUpdate"
$batPath  = "C:\Choi_Sales\98_Private\Claude\update.bat"

# Remove existing tasks (old Korean name + new English name)
Unregister-ScheduledTask -TaskName "MetalPrice_AutoUpdate" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "비철금속가격_자동업데이트" -Confirm:$false -ErrorAction SilentlyContinue

# Action
$action = New-ScheduledTaskAction -Execute $batPath

# Triggers: 09:00 ~ 17:00, every hour (9 triggers)
$triggers = 9..17 | ForEach-Object {
    New-ScheduledTaskTrigger -Daily -At "$($_):00"
}

# Settings
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
    -Trigger  $triggers `
    -Settings $settings `
    -Force | Out-Null

Write-Host "Done: $taskName registered (daily 09:00~17:00, every hour)"
schtasks /Query /TN $taskName /FO LIST 2>&1 | Select-String "Next Run|Status"
