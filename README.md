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
```

## 🐳 Docker

```powershell
docker compose up -d
```

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
| [ANDROID_INTEGRATION_GUIDE.md](ANDROID_INTEGRATION_GUIDE.md) | Android entegrasyon rehberi |
| [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) | Geliştirme iş akışı |

## 📄 Lisans

MIT — Detaylar için [LICENSE](LICENSE) dosyasına bakın.
