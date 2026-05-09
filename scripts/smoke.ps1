# smoke.ps1 — Calisan sunucuya karsi smoke testleri calistirir
# Kullanim: .\scripts\smoke.ps1
# NOT: Sunucunun http://127.0.0.1:8787 adresinde calistigindan emin olun.

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " BasketScoutDataService - Smoke Test" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".venv")) {
    Write-Host "Hata: .venv bulunamadi." -ForegroundColor Red
    exit 1
}

& ".venv\Scripts\python.exe" -m app.scripts.smoke_test

exit $LASTEXITCODE
