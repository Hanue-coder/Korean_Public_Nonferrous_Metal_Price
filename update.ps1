Set-Location $PSScriptRoot

# Skip if today's data already exists in CSV
$today = (Get-Date).ToString("yyyy-MM-dd")
$csv   = "$PSScriptRoot\data\prices.csv"

if (Test-Path $csv) {
    $exists = Select-String -Path $csv -Pattern "^$today," -Quiet
    if ($exists) {
        Write-Host "$today 데이터가 이미 존재합니다. 업데이트를 건너뜁니다."
        exit 0
    }
}

Write-Host "$today 데이터 없음 - 업데이트 시작"

& "$PSScriptRoot\pull.ps1"

& "C:\Users\USER\AppData\Local\Programs\Python\Python313\python.exe" "$PSScriptRoot\scrape_prices.py"

& "C:\Users\USER\AppData\Local\Programs\Python\Python313\python.exe" "$PSScriptRoot\generate_dashboard.py"

& "$PSScriptRoot\sync.ps1"
