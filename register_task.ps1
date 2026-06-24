# Run this script as Administrator to register the scheduled task

$taskName  = "비철금속가격_자동업데이트"
$scriptPath = "C:\최태성_영업\98_Private\Claude\update.bat"

$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>조달청 비철금속 가격 자동 업데이트 (매일 09:00~17:00, 1시간 간격)</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T09:00:00</StartBoundary>
      <Repetition>
        <Interval>PT1H</Interval>
        <Duration>PT8H</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Settings>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Actions>
    <Exec>
      <Command>$scriptPath</Command>
    </Exec>
  </Actions>
</Task>
"@

$xmlPath = "$env:TEMP\task_비철금속.xml"
$xml | Out-File -FilePath $xmlPath -Encoding Unicode

schtasks /Create /TN $taskName /XML $xmlPath /F

Remove-Item $xmlPath -ErrorAction SilentlyContinue

Write-Host ""
schtasks /Query /TN $taskName /FO LIST /V | Select-String "Repeat|Logon|Power|Stop Task|Last Result|Next Run"
