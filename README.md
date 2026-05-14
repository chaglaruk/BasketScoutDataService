# BasketScoutDataService

<p align="center">
  <strong>BasketScout Android Uygulaması için Self-Hosted Backend Veri Servisi</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.111%2B-009688?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLite-MVP-003B57?style=flat-square" alt="SQLite">
  <img src="https://img.shields.io/badge/lisans-MIT-green?style=flat-square" alt="MIT">
</p>

---

## 🎯 Amaç

BasketScoutDataService, İngiltere'deki bakkal ürünlerinin fiyatlarını toplar,
normalize eder ve Android uygulamasına REST API aracılığıyla sunar.

Her fiyat yanıtı; **kaynak**, **güven skoru** ve **son kontrol zamanı** içerir.

## ⚡ Tek Komutla Başlat

```powershell
.\scripts\dev.ps1
```

Bu komut:
- `.venv` sanal ortamını oluşturur (ilk çalıştırmada)
- Bağımlılıkları yükler
- SQLite veritabanını başlatır
- Demo veriyi ekler
- Sunucuyu `http://127.0.0.1:8787` adresinde başlatır

## 📡 API Endpoint'leri

| Endpoint | Yöntem | Açıklama |
|---|---|---|
| `/health` | GET | Sağlık kontrolü |
| `/providers/status` | GET | Provider durumları |
| `/products/search?q=milk` | GET | Ürün arama |
| `/prices/latest?product=milk&postcode=SE13` | GET | Fiyat sorgulama |
| `/basket/compare` | POST | Sepet karşılaştırma |
| `/admin/refresh` | POST | Provider yenileme |
| `/admin/runs` | GET | Run geçmişi |
| `/docs` | GET | Swagger UI |

## 🏗️ Mimari

```
FastAPI (8787)
    │
    ├── ProviderRegistry
    │       ├── MockProvider          ✓ Her zaman çalışır
    │       ├── ManualImportProvider  ✓ CSV yedek
    │       ├── OpenFoodFacts         ✓ Ürün meta verisi
    │       ├── OpenPrices            ~ İskelet (barkod gerekli)
    │       └── Retailer Providers    ~ LIMITED (JS/bot koruması)
    │
    ├── Services (ProductService, PriceService, BasketService)
    │
    └── SQLite (SQLAlchemy 2.x)
```

## 📊 Provider Durumları

| Provider | Durum | Açıklama |
|---|---|---|
| MockProvider | ✅ OK | Deterministik demo verisi |
| ManualImportProvider | ✅ OK | CSV'den yükler |
| OpenFoodFacts | ✅ OK | Ürün meta verisi |
| OpenPrices | ~ LIMITED | Barkod entegrasyonu gerekli |
| Tesco, Asda, Sainsbury's... | ~ LIMITED | JS render / bot koruması |

> **Önemli**: İngiltere süpermarketleri için garantili ücretsiz resmi fiyat API'si yoktur.
> Detaylar için [DATA_SOURCE_STRATEGY.md](DATA_SOURCE_STRATEGY.md) dosyasına bakın.

## 🧪 Test

```powershell
.\scripts\test.ps1   # pytest
.\scripts\lint.ps1   # ruff
.\scripts\smoke.ps1  # canlı endpoint smoke test (sunucu açık olmalı)
.\scripts\prod_smoke.ps1 -BaseUrl http://127.0.0.1:8787  # deployment smoke
```

## 🐳 Docker

```powershell
docker compose up -d
```

Production smoke:

```powershell
.\scripts\prod_smoke.ps1 -BaseUrl http://127.0.0.1:8787
```

## 🔐 Deployment Safety Notes

- Public deployment öncesi `ADMIN_TOKEN` ayarlanmalıdır.
- `ENV=production` modunda token yoksa `/admin/*` endpointleri `503` döner.
- `CORS_ALLOWED_ORIGINS` production'da explicit origin listesi olmalıdır (`*` önerilmez).
- Detaylı adımlar için `DEPLOYMENT_GUIDE.md` dosyasına bakın.

## 📁 Proje Yapısı

```
BasketScoutDataService/
  app/
    api/          → FastAPI route'ları
    core/         → Konfigürasyon, loglama, hata tipleri
    db/           → SQLAlchemy modelleri, repository'ler, seed
    domain/       → Pydantic modelleri, normalizasyon, güven skoru
    providers/    → Veri provider'ları (mock, CSV, open data, scraping)
    services/     → İş mantığı katmanı
    jobs/         → Zamanlanmış görevler
  tests/          → pytest test paketi
  scripts/        → PowerShell yardımcı scriptler
  data/           → Veritabanı ve CSV import'ları
```

## 📖 Belgeler

| Dosya | İçerik |
|---|---|
| [AGENTS.md](AGENTS.md) | Otonom ajan kuralları |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Teknik mimari |
| [API_CONTRACT.md](API_CONTRACT.md) | API sözleşmesi |
| [DATA_SOURCE_STRATEGY.md](DATA_SOURCE_STRATEGY.md) | Veri kaynağı stratejisi |
| [SCRAPING_POLICY.md](SCRAPING_POLICY.md) | Scraping politikası |
| [PROVIDER_STATUS.md](PROVIDER_STATUS.md) | Provider durum raporu |
| [ADMIN_SECURITY.md](ADMIN_SECURITY.md) | Admin endpoint güvenliği |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Remote deployment hazırlık rehberi |
| [ANDROID_INTEGRATION_GUIDE.md](ANDROID_INTEGRATION_GUIDE.md) | Android entegrasyon rehberi |
| [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) | Geliştirme iş akışı |

## 📄 Lisans

MIT — Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## Daily Web Observation (Milestone 27B)

- Job script: `python -m app.scripts.run_daily_price_observation`
- Dry-run: `python -m app.scripts.run_daily_price_observation --dry-run`
- Watchlist data source: `web_price_watchlist` table.
- Only exact configured URLs are attempted (no crawling/discovery).
- Stock remains `Unknown` for web observations.
- Public compare only uses rows with `public_display_allowed=true`.
- GitHub Actions workflow: `.github/workflows/daily-price-observation.yml`

Observation docs:

- `WEB_PRICE_OBSERVATION_POLICY.md`
- `WEB_PRICE_OBSERVATION_RUNBOOK.md`
- `WEB_PRICE_OBSERVATION_RESULTS.md`

## Scrapling Lab (Milestone 27E)

- AmaÃ§: parser dayanÄ±klÄ±lÄ±ÄŸÄ±nÄ± artÄ±rmak iÃ§in Scrapling tabanlÄ± deneysel gÃ¶zlem yolu.
- GÃ¼venli kapsam: exact watchlist URL, public sayfa, dÃ¼ÅŸÃ¼k frekans, internal-only varsayÄ±lan.
- Yasak: login/captcha/proxy/stealth bypass/private API.
- Komut:
  - `python -m app.scripts.run_daily_price_observation --provider scrapling --dry-run`
  - `python -m app.scripts.run_daily_price_observation --provider scrapling --force`

Opsiyonel kurulum:

```powershell
pip install "scrapling>=0.4.8"
# fetcher class'lari da gerekirse:
pip install "scrapling[fetchers]>=0.4.8"
```

Politika ve degerlendirme:

- `SCRAPLING_EVALUATION.md`
- `SCRAPLING_USAGE_POLICY.md`
