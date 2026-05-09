# lint.ps1 — Ruff ile kod kalite kontrolu
# Kullanim: .\scripts\lint.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host " BasketScoutDataService - Linter" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".venv")) {
    Write-Host "Hata: .venv bulunamadi." -ForegroundColor Red
    exit 1
}

Write-Host "ruff calistiriliyor..." -ForegroundColor Yellow
& ".venv\Scripts\ruff.exe" check app/ tests/

if ($LASTEXITCODE -eq 0) {
    Write-Host "Lint gecti." -ForegroundColor Green
} else {
    Write-Host "Lint hatalari bulundu." -ForegroundColor Red
    exit $LASTEXITCODE
}
