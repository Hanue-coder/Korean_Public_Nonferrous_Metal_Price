# Run as Administrator

$taskName = "비철금속가격_자동업데이트"
$batPath  = "C:\Choi_Sales\98_Private\Claude\update.bat"

# Remove existing task
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

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

Write-Host "등록 완료 - 매일 9시~17시 매 1시간 실행"
schtasks /Query /TN $taskName /FO LIST 2>&1 | Select-String "Next Run|Status"
