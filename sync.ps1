Set-Location $PSScriptRoot

git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "Nothing to commit."
    exit 0
}

# Stash local changes, pull remote (prefer ours on conflict), reapply
git stash
git pull --no-rebase -X ours
git stash pop

# Re-add after stash pop
git add -A
$status2 = git status --porcelain
if (-not $status2) {
    Write-Host "Nothing to commit after pull."
    exit 0
}

git commit -m "chore: auto update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git -c credential.interactive=never push
exit $LASTEXITCODE
