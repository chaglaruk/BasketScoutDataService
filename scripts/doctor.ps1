# doctor.ps1 — Gelistirme ortamini kontrol eder
# Kullanim: .\scripts\doctor.ps1

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " BasketScoutDataService - Doctor Check" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$Passed = 0
$Failed = 0

function Check($label, $condition, $fix = $null) {
    if ($condition) {
        Write-Host "  [OK] $label" -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host "  [!!] $label" -ForegroundColor Red
        if ($fix) { Write-Host "       Cozum: $fix" -ForegroundColor Yellow }
        $script:Failed++
    }
}

# Python
$pyVersion = & python --version 2>&1
Check "Python yuklu" ($pyVersion -match "Python 3\.1[1-9]") "Python 3.11+ yukleyin"

# .venv
Check ".venv mevcut" (Test-Path ".venv") ".\scripts\dev.ps1 calistirin"

# .env
Check ".env mevcut" (Test-Path ".env") "cp .env.example .env"

# requirements.txt
Check "requirements.txt mevcut" (Test-Path "requirements.txt") "git pull"

# DB dizini
Check "data/ dizini mevcut" (Test-Path "data") ".\scripts\dev.ps1 calistirin"

# app/main.py
Check "app/main.py mevcut" (Test-Path "app\main.py") "git clone tekrarlayın"

# Sunucu ping
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8787/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Check "Sunucu calisıyor (http://127.0.0.1:8787)" ($r.StatusCode -eq 200) ""
} catch {
    Check "Sunucu calisıyor (http://127.0.0.1:8787)" $false ".\scripts\dev.ps1 calistirin"
}

Write-Host ""
Write-Host "--------------------------------------" -ForegroundColor Gray
Write-Host "  Gecen: $Passed  |  Basarisiz: $Failed" -ForegroundColor White
Write-Host ""

if ($Failed -gt 0) { exit 1 }
