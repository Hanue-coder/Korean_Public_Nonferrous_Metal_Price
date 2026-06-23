[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$outputCsv = "C:\Users\USER\Desktop\aluminum_prices.csv"
$logFile   = "C:\Users\USER\Desktop\scrape_log.txt"
$ua = "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36"
$baseUrl = "https://www.pps.go.kr"

function Write-Log($msg) {
    $line = "$(Get-Date -Format 'HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

Remove-Item $logFile -ErrorAction SilentlyContinue
Write-Log "Starting scraper (full history)"

# Step 1: collect ALL bbsSn from all list pages
$r0 = Invoke-WebRequest -Uri "$baseUrl/bichuk/bbs/list.do?key=00825&pageIndex=1" -UseBasicParsing -UserAgent $ua -TimeoutSec 30
$countMatch = [regex]::Match($r0.Content, 'txt-color-darken">(\d[\d,]+)</span>')
$total = [int]($countMatch.Groups[1].Value -replace ',','')
$pageCount = [Math]::Ceiling($total / 10)
Write-Log "Total: $total posts, $pageCount pages"

$allSns = New-Object System.Collections.Generic.List[string]
for ($pg = 1; $pg -le $pageCount; $pg++) {
    try {
        $r = Invoke-WebRequest -Uri "$baseUrl/bichuk/bbs/list.do?key=00825&pageIndex=$pg" -UseBasicParsing -UserAgent $ua -TimeoutSec 30
        $ms = [regex]::Matches($r.Content, "goView\('(\d+)',\s*'0001'\)")
        foreach ($m in $ms) { $allSns.Add($m.Groups[1].Value) }
        if ($pg % 50 -eq 0) { Write-Log "List $pg/$pageCount (total sns: $($allSns.Count))" }
    } catch { Write-Log "List page $pg error: $_" }
    Start-Sleep -Milliseconds 200
}
Write-Log "All bbsSns collected: $($allSns.Count)"

# Step 2: fetch detail pages - get date from page, extract first price
Set-Content -Path $outputCsv -Value "date,price_ton_incl_vat,kg_excl_vat,kg_incl_vat" -Encoding UTF8
$i = 0; $ok = 0
foreach ($sn in $allSns) {
    $i++
    try {
        $r = Invoke-WebRequest -Uri "$baseUrl/bichuk/bbs/view.do?key=00825&bbsSn=$sn" -UseBasicParsing -UserAgent $ua -TimeoutSec 30

        # Get date from the price table (판매기간 column: YYYY.MM.DD)
        $dtMatch = [regex]::Match($r.Content, '(\d{4})\.(\d{2})\.(\d{2})</td>')
        if (-not $dtMatch.Success) { continue }
        $dateStr = "$($dtMatch.Groups[1].Value)-$($dtMatch.Groups[2].Value)-$($dtMatch.Groups[3].Value)"

        # Skip if before 2012-01-06
        if ($dateStr -lt "2012-01-06") { continue }

        # Extract first plausible aluminum price (1,000,000 ~ 50,000,000 won/ton)
        $priceMs = [regex]::Matches($r.Content, '(\d[\d,]+)[^<]{0,10}</td>')
        foreach ($pm in $priceMs) {
            $pStr = $pm.Groups[1].Value -replace ',',''
            if ($pStr.Length -ge 7) {
                $ton = [long]$pStr
                if ($ton -ge 1000000 -and $ton -le 50000000) {
                    $kgExcl = [Math]::Round($ton / 1.1 / 1000)
                    $kgIncl = [Math]::Round($ton / 1000)
                    Add-Content -Path $outputCsv -Value "$dateStr,$ton,$kgExcl,$kgIncl" -Encoding UTF8
                    $ok++
                    break
                }
            }
        }
        if ($i % 200 -eq 0) { Write-Log "Detail $i/$($allSns.Count) (saved: $ok)" }
    } catch { Write-Log "Error [$sn]: $_" }
    Start-Sleep -Milliseconds 300
}
Write-Log "DONE. $ok records saved to $outputCsv"
