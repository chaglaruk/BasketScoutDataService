# test.ps1 — Testleri calistirir
# Kullanim: .\scripts\test.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host " BasketScoutDataService - Test Suite" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".venv")) {
    Write-Host "Hata: .venv bulunamadi. Once .\scripts\dev.ps1 calistirin." -ForegroundColor Red
    exit 1
}

Write-Host "pytest calistiriliyor..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m pytest tests/ -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "TÜM TESTLER GECTI" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "BAZI TESTLER BASARISIZ" -ForegroundColor Red
    exit $LASTEXITCODE
}
