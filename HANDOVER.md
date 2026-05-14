# HANDOVER.md — El Teslimi Belgesi

Her anlamlı milestone sonrasında güncellenir.

---

## Son Güncelleme

Tarih: 2026-05-09
Milestone: Tam Kurulum ve Son Audit

## Proje Durumu: WORKING

**ÇALIŞIYOR** — Tüm testler ve linter (Ruff) geçmektedir.

- **GitHub Repo URL:** https://github.com/chaglaruk/BasketScoutDataService
- **Güncel Commit Hash:** `bd0be06116ebc0920607c5930078d5bf7f963687`
- **Sunucu Durumu:** Çalışıyor (http://127.0.0.1:8787)
- **Endpoint Durumu (Smoke Test):** Başarılı (5/5)
  - `GET /health` (OK)
  - `GET /providers/status` (OK)
  - `GET /products/search?q=milk` (OK)
  - `GET /prices/latest?product=milk&postcode=SE13` (OK)
  - `POST /basket/compare` (OK)

## Tamamlanan Milestones

| Milestone | Durum | Açıklama |
|---|---|---|
| 0 — Proje Kurulumu | ✅ | Dizin yapısı, git, konfigürasyon |
| 1 — Mock API | ✅ | /health, /providers, /products, /prices, /basket |
| 2 — Provider Mimarisi | ✅ | BaseProvider, ProviderRegistry, cache politikası |
| 3 — Açık Veri Provider'ları | ✅ | OpenFoodFacts, OpenPrices iskelet |
| 4 — Scraping Spike | ✅ | 8 retailer iskelet, tümü LIMITED |
| 5 — Scheduler | ✅ | APScheduler, /admin/refresh, /admin/runs |
| 6 — Android Sözleşmesi | ✅ | API_CONTRACT.md, ANDROID_INTEGRATION_GUIDE.md |
| 7 — Yerel Dev El Teslimi | ✅ | scripts/dev.ps1, test.ps1, vb. |
| 8 — Final QA & Audit | ✅ | GitHub entegrasyonu, smoke test, linting |
| 9 — Real-data capability | ✅ | OpenPrices, Manuel Import scripti, Tesco safe probe |
| 10 — QA & Provider Hardening | ✅ | Safe probe kalitesi, sepet şeffaflığı, artifact'ler |

## Provider Özeti ve Veri Doğruluğu (Real vs Mock)

**ÖNEMLİ:** İngiltere süpermarketleri için garantili, ücretsiz, canlı API bulunmamaktadır. Sistemin canlı (gerçek) fiyat dönmediği, `mock` olarak çalıştığı açıkça belirtilmiştir.

| Provider | Tip | Durum | Veri Niteliği |
|---|---|---|---|
| mock | mock | ✅ OK | Sadece Mock/Demo verisi |
| manual_import | manual | ✅ OK | CSV'den statik fiyat verisi |
| open_food_facts | open_data | ✅ OK | Gerçek Açık Veri (Sadece meta veri, fiyat YOK) |
| open_prices | open_data | ~ LIMITED | Gerçek Açık Veri İskeleti (Barkod gerektiriyor) |
| tesco | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| asda | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| sainsburys | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| morrisons | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| waitrose | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| coop | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| aldi | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| lidl | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |

## Sonraki Önerilen Milestone

**Playwright & Headless Browser Entegrasyonu:**
Mevcut `ScrapingBaseProvider` iskeletlerinin, JS-rendered (React/SPA) ve bot korumalı süpermarket sayfalarını geçebilmesi için projeye `playwright` veya `selenium base` entegre edilerek (örneğin ilk olarak Tesco ve Sainsbury's üzerinde) gerçek zamanlı ağ taraması yeteneği kazandırılması.

## Milestone 26 Completed
Implemented provider priority (Manual > OpenPrices > Tesco > Mock). Enhanced API metadata with provider status summary and low-confidence counts.

## Milestone 27 Completed
Backend diagnostics wording polished for users. Store details show formatted source/confidence.

## Milestone 28 Completed
Implemented manual price management admin endpoints (/admin/manual-prices/*). Added provider priority visibility and Android diagnostics integration.

## Milestone 29 Completed
Hardened admin endpoints with optional ADMIN_TOKEN security (X-Admin-Token header). Added validation tests and documentation (ADMIN_SECURITY.md). Verified Android integration and fallback stability.

## Milestone 30 Completed
Hardened config parsing for `DEBUG` env collisions. Backend now safely maps `DEBUG=release|prod|production` to `False` and `DEBUG=development|dev` to `True`, preventing test/startup failures from global environment variables. Added regression tests in `tests/test_config.py`.

## Milestone 30 - Deployment Readiness Completed
Prepared backend for remote deployment without locking to a hosting provider. Added production-safe config aliases (`HOST/PORT/ENV`), DB fallback (`DATABASE_URL` or `SQLITE_PATH`), configurable CORS allow-list, production admin-token enforcement behavior for `/admin/*`, deployment guide (`DEPLOYMENT_GUIDE.md`), and `scripts/prod_smoke.ps1` for production-style validation.

---

## Milestone 26A/26B - Real data visibility and deployment readiness

Date: 2026-05-13

Status: REAL_DATA_VISIBLE_LOCAL_ONLY.

What changed:
- Manual/imported CSV data is now preferred over OpenPrices, Tesco limited, and mock fallback.
- Mock provider is queried only for product names not resolved by non-mock providers.
- `/basket/compare` metadata now exposes `provider_used`, `confidence`, `last_checked_at`, `freshness`, `why_mock_used`, `stock_status`, and `line_source_summary`.
- `/providers/reality` exposes implementation, price/stock capability, freshness, confidence, safety constraints, and next safe step per provider/source.
- Manual CSV seed rows now include retailer display names and manual `last_checked_at` values.
- Stock is still `Unknown` unless a provider returns reliable availability. No guaranteed live stock is claimed.

Validation:
- Backend tests: `.venv\\Scripts\\python.exe -m pytest -q` -> 58 passed.
- Backend lint: `.venv\\Scripts\\python.exe -m ruff check .` -> passed.
- Local smoke: `scripts\\smoke.ps1` -> passed 5/5.
- Production-style smoke: `scripts\\prod_smoke.ps1 -SkipAdminChecks` -> passed.
- Local API: `http://127.0.0.1:8787/health` -> ok.

Sample responses saved locally:
- `artifacts/real-price-20260513-223630/milk-bread-eggs.json` -> manual_import, winner Aldi, 100% coverage, stock unknown.
- `artifacts/real-price-20260513-223630/bananas-pasta-rice.json` -> manual_import, winner Aldi, 100% coverage, stock unknown.
- `artifacts/real-price-20260513-223630/chicken-toilet-roll.json` -> manual_import, winner Aldi, 100% coverage, stock unknown.
- `artifacts/real-price-20260513-223630/providers-reality.json`.

Deployment decision:
- No paid/unknown remote deployment was performed.
- Recommended next hosting path: Dockerized VPS or Render/Railway-style ASGI host with HTTPS, persistent SQLite/Postgres, env vars, and `ADMIN_TOKEN` set.
- cPanel/shared hosting remains unsuitable unless it supports long-running Python ASGI apps.

---

## Milestone 26C - Data feed operations and provider reality cleanup

Date: 2026-05-14

Status: DATA_FEED_OPERATIONS_READY.

What changed:
- Added manual CSV validation/import/export workflow for admin operations.
- Added `MANUAL_PRICE_FEED.md` with CSV schema, CLI commands, validation report fields, and stock policy.
- Added `scripts/manual_feed.ps1` and expanded `python -m app.scripts.import_csv` with `validate`, `import`, `export`, and `summary` commands.
- Expanded `data/manual_import/sample_prices.csv` to 37 validated rows covering the MVP grocery set.
- Added route warnings when a provider-specific `/prices/latest` query returns no rows.
- OpenPrices now uses OpenFoodFacts barcode candidates and GBP OpenPrices rows where available, but remains partial/open/historical.
- Tesco remains a low-confidence public-page probe only; no login/captcha/private API bypass is used.
- Mock provider no longer reports reliable stock; mock availability is `Unknown` in API output.
- Runtime SQLite WAL/SHM files were removed from git tracking and ignored.

Validation:
- Backend tests: `.venv\Scripts\python.exe -m pytest -q` -> 66 passed.
- Backend lint: `.venv\Scripts\python.exe -m ruff check .` -> passed.
- Manual CSV validation: 37 total, 37 valid, 0 invalid, 0 duplicate, 0 stale.
- Smoke: `scripts\smoke.ps1` -> passed 5/5.
- Prod smoke: `scripts\prod_smoke.ps1 -SkipAdminChecks` -> passed.

Backend artifacts:
- `artifacts/provider-ops-20260514-131905/milk-bread-eggs-basket-compare.json`
- `artifacts/provider-ops-20260514-131905/bananas-pasta-rice-basket-compare.json`
- `artifacts/provider-ops-20260514-131905/chicken-toilet-roll-basket-compare.json`
- `artifacts/provider-ops-20260514-131905/open-prices-milk.json`
- `artifacts/provider-ops-20260514-131905/tesco-milk.json`
- `artifacts/provider-ops-20260514-131905/providers-reality.json`

Observed provider behavior:
- MVP sample baskets returned `manual_import` data and stock Unknown.
- OpenPrices milk query returned no usable row and now includes a warning/fallback reason.
- Tesco milk query returned one low-confidence limited row with stock Unknown.

Remaining blocker:
- Broader guaranteed live price/stock coverage requires official/licensed retailer feeds or data partnerships. It is not solved by scraping without bypassing retailer protections.

## Milestone 27B Completed

Implemented GitHub-hosted daily tracked web observation pipeline:

- Added `web_price_watchlist` and `price_observation` data model support.
- Added safe adapters for Tesco/Aldi/Sainsbury's/Lidl (tracked URLs only).
- Added `python -m app.scripts.run_daily_price_observation` with machine-readable report and log outputs.
- Added provider integration (`web_observation`) using only public-display-allowed observations.
- Added provider diagnostics fields for daily observation status.
- Added GitHub Actions workflow `.github/workflows/daily-price-observation.yml` (cron + manual dispatch + artifact upload + issue create/update).
- Added policy/runbook/results documentation for non-bypass, low-risk operation.

Current watchlist seeds are intentionally unconfigured (`enabled=false`, no exact URL) until safe exact URLs are explicitly documented.

## Milestone 27C Guncellemesi

- Watchlist CSV import/export araci eklendi:
  - `python -m app.scripts.import_web_price_watchlist <csv_path>`
  - `python -m app.scripts.export_web_price_watchlist [--template]`
- 4 perakendeci x 8 hedef urun icin baslangic watchlist CSV'si eklendi.
- URL politikasi uygulandi: dokumante edilmis kesin urun URL'si olmayan satirlar `enabled=false` kalir ve not ile isaretlenir.
- Gunluk observation issue icerigi artik `retailer/product/url/failure_type/suggested_safe_action` alanlarini icerir.
- Provider status cevabina `configured_url_count`, `missing_url_count`, `last_attempted_urls`, `last_successful_observations` alanlari eklendi.

## Milestone 27D Guncellemesi

- Arastirma dokumanindan 4 exact milk URL satiri iceren controlled seed CSV eklendi.
- Preflight policy/robots kontrolu calistirildi; sadece Aldi URL'si enabled edildi.
- Dry-run ve real-run observation denemesi yapildi.
- Real-run sonucu: Aldi URL'de `BLOCKED_BY_ACCESS_CONTROL`, gozlemlenen fiyat yok.
- Provider status alanlari genisletildi:
  - `enabled_url_count`
  - `attempted_url_count`
  - `observed_price_count`
  - `blocked_by_policy_count`
  - `blocked_by_access_count`
- Tum web observation kayitlari icin stock `Unknown` kalir; public compare icin `public_display_allowed=true` onayi gereklidir.

## Milestone 27E Guncellemesi

- Scrapling lab icin yeni servis eklendi:
  - `app/services/scrapling_price_observation_service.py`
  - `app/providers/scrapling_observation_provider.py`
- Gunluk script provider secimi alir:
  - `python -m app.scripts.run_daily_price_observation --provider default|scrapling`
- Scrapling config bayraklari eklendi:
  - `SCRAPLING_ENABLED` (default `true`)
  - `SCRAPLING_NETWORK_ENABLED` (default `true`)
  - `SCRAPLING_TIMEOUT_SECONDS`
  - `SCRAPLING_PUBLIC_CONFIDENCE_THRESHOLD`
- `/providers/status` Scrapling availability ve run metrikleri ile genisletildi.
- Fixture tabanli parser testleri eklendi (`tests/fixtures/scrapling/*`).
- SAFE policy korundu: login/captcha/proxy/stealth/private API bypass yok, stock `Unknown`.
