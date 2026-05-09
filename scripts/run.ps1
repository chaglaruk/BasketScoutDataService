# run.ps1 — Sunucuyu dogrudan baslatir (dev ortami olmadan)
# Kullanim: .\scripts\run.ps1

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

& ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8787
