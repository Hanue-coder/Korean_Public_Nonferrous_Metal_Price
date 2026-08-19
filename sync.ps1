Set-Location $PSScriptRoot
git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "Nothing to commit."
    exit 0
}
git commit -m "chore: auto update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git -c credential.interactive=never push
exit $LASTEXITCODE
