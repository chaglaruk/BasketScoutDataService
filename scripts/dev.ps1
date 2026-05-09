# dev.ps1 — Gelistirme sunucusunu baslatir
# Kullanim: .\scripts\dev.ps1
#
# Yapar:
# 1. .venv yoksa olusturur
# 2. Bagimlilikları yukler
# 3. SQLite DB yoksa olusturur
# 4. Demo veri ekler
# 5. FastAPI sunucusunu http://127.0.0.1:8787 adresinde baslatir

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " BasketScoutDataService - Dev Server" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Sanal ortam
if (-not (Test-Path ".venv")) {
    Write-Host "[1/5] Sanal ortam olusturuluyor (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "[1/5] Sanal ortam mevcut." -ForegroundColor Green
}

# 2. Bagimliliklar
Write-Host "[2/5] Bagimliliklar yukleniyor..." -ForegroundColor Yellow
& ".venv\Scripts\pip.exe" install -r requirements.txt --quiet

# 3. .env kontrol
if (-not (Test-Path ".env")) {
    Write-Host "[3/5] .env dosyasi olusturuluyor (.env.example kopyalanıyor)..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "[3/5] .env mevcut." -ForegroundColor Green
}

# 4. Veritabani ve seed
Write-Host "[4/5] Veritabani baslatiliyor..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m app.scripts.seed_demo_data

# 5. Sunucu
Write-Host ""
Write-Host "[5/5] Sunucu baslatiliyor..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:   http://127.0.0.1:8787" -ForegroundColor Green
Write-Host "  Docs:  http://127.0.0.1:8787/docs" -ForegroundColor Green
Write-Host "  Saglik: http://127.0.0.1:8787/health" -ForegroundColor Green
Write-Host ""
Write-Host "Durdurmak icin Ctrl+C" -ForegroundColor Yellow
Write-Host ""

& ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload
