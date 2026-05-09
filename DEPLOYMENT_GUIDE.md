# DEPLOYMENT_GUIDE.md - Uzak Sunucu Hazirlik Rehberi

Bu belge, BasketScoutDataService'i **belirli bir hosting'e kilitlemeden** guvenli sekilde yayinlamaya hazirlamak icindir.

## 1. Hedef ve Kapsam

- Amaç: Servisi remote ortamda calisabilir hale getirmek.
- Kapsam disi: Crawler bypass, captcha bypass, login/paywall bypass, garantili canli market fiyati iddiasi.
- Veri gercegi: `mock` fallback her zaman korunur; canli fiyat garantisi yoktur.

## 2. Ortam Degiskenleri

Minimum production degiskenleri:

- `ENV=production`
- `HOST=0.0.0.0`
- `PORT=8787`
- `DATABASE_URL=...` veya `SQLITE_PATH=...`
- `ADMIN_TOKEN=<guclu-random-token>`
- `REQUIRE_ADMIN_TOKEN_IN_PRODUCTION=true`
- `CORS_ALLOWED_ORIGINS=https://uygulama-domaini`
- `LOG_LEVEL=INFO`
- `DEBUG=false`

Notlar:

- `HOST/PORT/ENV` ile birlikte legacy `APP_HOST/APP_PORT/APP_ENV` halen desteklenir.
- `DATABASE_URL` yoksa servis `SQLITE_PATH` uzerinden SQLite URL olusturur.
- `CORS_ALLOWED_ORIGINS` comma-separated listedir. Production'da `*` onerilmez.

## 3. Local Calistirma (Gelþtirme)

```powershell
.\scripts\dev.ps1
```

Saglik kontrolu:

```powershell
Invoke-WebRequest http://127.0.0.1:8787/health
```

## 4. Windows Uzerinde Dogrudan Calistirma

```powershell
.\scripts\run.ps1
```

Alternatif:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

## 5. Docker Ile Calistirma

```powershell
docker compose up -d --build
```

Dogrulama:

```powershell
docker compose ps
docker compose logs -f api
```

Production deployment oncesi:

- Host ortaminda `ADMIN_TOKEN` set edin.
- `CORS_ALLOWED_ORIGINS` degerini gercek domainlerle sinirlayin.

## 6. VPS Deployment Outline

1. Sunucuya repo clone edin.
2. Firewall'da sadece gerekli portlari acin (tercihen sadece reverse proxy portlari).
3. Ortam degiskenlerini `.env` veya servis yoneticisi (systemd/docker) uzerinden verin.
4. Backend'i private networkte dinletin (`127.0.0.1` veya container network).
5. Nginx/Caddy ile ters proxy kurun.
6. TLS/HTTPS aktif edin (Let's Encrypt vb.).
7. `health` ve `prod_smoke` ile dogrulayin.

## 7. cPanel Notlari

- cPanel paylasimli ortamlarda uzun sureli ASGI/FastAPI sureci sinirli veya sorunlu olabilir.
- Root/daemon erisimi yoksa stabil backend operasyonu zorlasir.
- Daha stabil secenek: Docker destekli VPS veya PaaS (ASGI sureci destekleyen).

## 8. Admin Endpoint Guvenligi

- Production modunda (`ENV=production`) `ADMIN_TOKEN` yoksa `/admin/*` endpointleri `503` doner.
- `ADMIN_TOKEN` setli ise token'siz/yanlis tokenli istek `401` doner.
- Admin endpointleri public internete aciliyorsa reverse proxy ile IP kisitlamasi ekleyin.

## 9. Health ve Provider Dogrulama

Zorunlu kontrol endpointleri:

- `GET /health`
- `GET /providers/status`
- `GET /prices/latest?product=milk`

Beklentiler:

- `health.ok == true`
- `providers` listesi bos olmamali
- Price item'larinda `source`, `confidence`, `last_checked_at` alanlari olmali

## 10. Smoke Testler

Local smoke:

```powershell
.\scripts\smoke.ps1
```

Production-style smoke:

```powershell
.\scripts\prod_smoke.ps1 -BaseUrl https://api.example.com
```

Admin token ile:

```powershell
.\scripts\prod_smoke.ps1 -BaseUrl https://api.example.com -AdminToken "<token>"
```

## 11. Reverse Proxy Notlari

- `/health` endpointini uptime probe icin acik tutun.
- `X-Forwarded-*` headerlari reverse proxy tarafinda dogru gecsin.
- Gereksiz HTTP methodlari ve buyuk body boyutlari proxy tarafinda kisitlanabilir.

## 12. HTTPS Onerisi

Production'da her zaman HTTPS kullanin:

- Token'larin acik metin tasinmasini onler.
- Mobil istemci trafigi icin guvenli kanal saglar.

## 13. Loglama ve Troubleshooting

- `LOG_LEVEL=INFO` ile baslayin (`DEBUG` sadece gecici).
- Docker: `docker compose logs -f api`
- Common issues:
  - `401` admin: `X-Admin-Token` eksik/yanlis
  - `503` admin: production'da `ADMIN_TOKEN` set edilmemis
  - Bos fiyat listesi: provider durumlarini `/providers/status` ile kontrol edin
  - CORS problemi: `CORS_ALLOWED_ORIGINS` domain listesi eksik veya yanlis
