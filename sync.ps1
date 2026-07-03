Set-Location $PSScriptRoot
git add -A
git commit -m "자동 업데이트 $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git -c credential.interactive=never push
