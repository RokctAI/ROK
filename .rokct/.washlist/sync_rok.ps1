# ROK Local Sync & Deploy Script
# Located under: ROK/.rokct/.washlist/sync_rok.ps1

# Dynamically resolve path relative to script location
$ROK_PATH = Resolve-Path (Join-Path $PSScriptRoot "..\..")

Write-Host "🧼 Running Washlist Rebranding sweeps (Case-Aware Renames)..." -ForegroundColor Cyan
python "$ROK_PATH\.rokct\.washlist\washlist_run.py"

Write-Host "✅ Rebrand sweep complete! Your local ROK repository ($ROK_PATH) is cleanly processed." -ForegroundColor Green
