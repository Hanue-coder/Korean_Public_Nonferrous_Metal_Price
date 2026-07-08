Set-Location $PSScriptRoot

# Skip if today's data already exists in CSV
$today = (Get-Date).ToString("yyyy-MM-dd")
$csv   = "$PSScriptRoot\data\prices.csv"

if (Test-Path $csv) {
    $exists = Select-String -Path $csv -Pattern "^$today," -Quiet
    if ($exists) {
        Write-Host "$today data already exists. Skipping."
        exit 0
    }
}

Write-Host "$today - starting update"

# Use explicit Python path (Windows Store stub fails in non-interactive scheduled tasks)
$python = "C:\Users\seren\AppData\Local\Python\bin\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "ERROR: Python not found at $python"
    exit 1
}

Write-Host "Using Python: $python"

& $python "$PSScriptRoot\scrape_prices.py"
& $python "$PSScriptRoot\generate_dashboard.py"
& $python "$PSScriptRoot\generate_issues.py"
& "$PSScriptRoot\sync.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Push failed (exit $LASTEXITCODE), retrying in 30s..."
    Start-Sleep -Seconds 30
    & "$PSScriptRoot\sync.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Push failed after retry. Exit $LASTEXITCODE"
        exit 1
    }
}

Write-Host "Done: push verified OK"
