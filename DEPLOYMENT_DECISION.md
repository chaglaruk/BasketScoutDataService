# BasketScoutDataService Deployment Decision

Son guncelleme: 2026-05-13

Milestone 26B amaci, remote backend icin hazirlik yapmak ve Android tarafinda Local ADB / Remote / Offline mode gecisini desteklemektir. Bu dokuman aktif deployment karari degildir; ucretli/manuel hesap gerektiren deployment kullanici onayi olmadan yapilmaz.

## Secenek degerlendirmesi

| Secenek | Maliyet / free tier | SQLite kalicilik | Env var | HTTPS | Background job | Limitler | Karar |
|---|---|---:|---:|---:|---:|---|---|
| Local only | Ucretsiz | Evet, lokal disk | `.env` | Hayir | Lokal scheduler | Telefon icin `adb reverse` gerekir | Gelistirme icin varsayilan |
| Dockerized VPS | Ucretli VPS | Evet, volume | Evet | Reverse proxy ile | Evet | Bakim/guvenlik kullanici sorumlulugu | En guvenilir production aday |
| Render Free | Ucretsiz preview | Hayir, free web service filesystem ephemeral; free Postgres 30 gun | Evet | Evet | Sinirli | Idle spin-down, outbound limits, free disk yok | Demo icin uygun, kalici SQLite icin uygun degil |
| Railway | Free $1 resource credit / Hobby $5 | Volume ucretli | Evet | Evet | Evet | Free kredi cok sinirli | Kisa demo icin uygun; surekli backend icin maliyet kontrolu gerekir |
| Fly.io | Pay-as-you-go, kredi karti gerekir | Volume ucretli | Evet | Evet | Evet | Free tier yok / kart gerekir | Onay olmadan deploy edilmez |
| cPanel/shared hosting | Hosting paketine bagli | Belirsiz | Belirsiz | Hostinge bagli | Genelde sinirli | FastAPI/ASGI yerine WSGI/Passenger kisitlari olabilir | Uygunluk hostinge bagli; onerilen ana yol degil |
| Other free/safe | Degisken | Degisken | Degisken | Degisken | Degisken | Hizmet sartlarina bagli | Ayrica incelenmeli |

## Oneri

1. Simdilik `Local ADB` varsayilan kalsin.
2. Android uygulama `Remote` URL modunu desteklesin, ancak remote basarisi fake edilmesin.
3. Ucret/onay gerektirmeyen hazir remote provider yoksa deployment yapilmasin.
4. Production icin en saglam yol: Docker + VPS veya kalici Postgres destekleyen managed platform.
5. Render Free sadece demo icin dusunulebilir; SQLite dosyasi kalici olmaz.

## Production readiness gereksinimleri

- `HOST` / `PORT` veya `APP_HOST` / `APP_PORT`
- `ENV` veya `APP_ENV`
- `DATABASE_URL` veya `SQLITE_PATH`
- `ADMIN_TOKEN`
- `CORS_ALLOWED_ORIGINS`
- `LOG_LEVEL`
- Provider toggle/priority dokumantasyonu
- `/health`
- `/providers/status`
- `/providers/reality`
- Production smoke script

## Guvenlik notlari

- Production'da admin endpointleri `ADMIN_TOKEN` olmadan kullanilamaz olmalidir.
- Production CORS wildcard olmamali.
- Secret commit edilmez.
- Retailer scraping bot koruma/captcha/login bypass yapmaz.

## Kaynaklar

- Render Free docs: free web service idle spin-down, ephemeral filesystem, persistent disk yok.
- Railway pricing docs: Free $1 resource credit, volume storage ucreti.
- Fly.io pricing docs: kredi karti gerekir, volume ucretlidir.
- cPanel support docs: Python uygulamalari WSGI/Passenger veya host ozelligine baglidir.

---

## Milestone 26 decision addendum - 2026-05-13

Decision: deployment-ready local-only, awaiting selected host.

Actual remote deployment: not performed.

Reason:
- No already-approved free/safe hosting target with secrets was available in this environment.
- Paid/unknown service deployment requires explicit user approval.
- Admin endpoints must not be exposed publicly without `ADMIN_TOKEN` and HTTPS.

Recommended path:
1. Dockerized VPS or Render/Railway-style ASGI host with persistent storage.
2. Configure `ADMIN_TOKEN`, `ENV=production`, `CORS_ALLOWED_ORIGINS`, and persistent DB path/URL.
3. Run `scripts/prod_smoke.ps1 -BaseUrl <remote-url> -AdminToken <token>`.
4. Enter the HTTPS URL in Android Settings -> More -> Data source mode -> Remote.

cPanel/shared hosting remains not recommended unless it supports long-running ASGI processes, environment variables, HTTPS, and persistent storage.
