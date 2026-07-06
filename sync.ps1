Set-Location $PSScriptRoot
git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "Nothing to commit."
    exit 0
}
git commit -m "자동 업데이트 $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git -c credential.interactive=never push
exit $LASTEXITCODE
