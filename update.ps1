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

& "$PSScriptRoot\pull.ps1"
& $python "$PSScriptRoot\scrape_prices.py"
& $python "$PSScriptRoot\generate_dashboard.py"
& "$PSScriptRoot\sync.ps1"
