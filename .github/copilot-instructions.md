# BasketScoutDataService — GitHub Copilot Talimatları

Bu dosya, GitHub Copilot ve diğer AI asistanlarına proje bağlamı sağlar.

## Proje Amacı

BasketScout Android uygulaması için self-hosted backend veri servisi.
Bakkal ürün fiyatlarını toplar, normalize eder ve karşılaştırır.

## Stack

- Python 3.11+, FastAPI, Uvicorn
- SQLite + SQLAlchemy 2.x ORM
- Pydantic v2 veri modelleri
- httpx HTTP istemcisi
- BeautifulSoup4 HTML ayrıştırma
- APScheduler zamanlanmış görevler
- pytest + ruff test ve linting

## Kritik Kurallar

- `.env` dosyasına sır/API anahtarı ekleme — yalnızca `.env.example` kullan
- Provider hatalarını izole et — bir provider diğerlerini çökertmemeli
- Her API yanıtı: source, confidence, last_checked_at içermeli
- Captcha, login veya bot koruma bypass yapma
- Robotlar.txt'e saygı göster
- Scraping: rate limit, cache, açık sayfalar sadece
- Canlı scraping sınırlı/engellendiğinde mock veya cache kullan

## Provider Mimarisi

```
BaseProvider (ABC)
  ├── MockProvider          — deterministik demo, her zaman çalışır
  ├── ManualImportProvider  — CSV kaynaklı yedek
  ├── OpenFoodFactsProvider — ürün meta verisi (fiyat yok)
  ├── OpenPricesProvider    — kitlesel kaynak (güven: 0.6 tavan)
  └── retailers/
        ├── TescoProvider    [LIMITED]
        ├── AsdaProvider     [LIMITED]
        ├── SainsburysProvider [LIMITED]
        ├── MorrisonsProvider [LIMITED]
        ├── WaitroseProvider [LIMITED]
        ├── CoopProvider     [LIMITED]
        ├── AldiProvider     [LIMITED]
        └── LidlProvider     [LIMITED]
```

## API Endpoint'leri

- `GET /health` — sağlık kontrolü
- `GET /providers/status` — provider durumu
- `GET /products/search?q=milk` — ürün arama
- `GET /prices/latest?product=milk&postcode=SE13` — fiyat sorgulama
- `POST /basket/compare` — sepet karşılaştırma
- `POST /admin/refresh` — provider yenileme (yerel/dev)
- `GET /admin/runs` — run geçmişi

## Tek Komutla Başlatma

```powershell
.\scripts\dev.ps1
```

## Dosya Yapısı Özeti

- `app/` — ana uygulama kodu
- `app/providers/` — veri provider'ları
- `app/services/` — iş mantığı katmanı
- `app/api/` — FastAPI route'ları
- `app/domain/` — Pydantic modelleri ve iş kuralları
- `tests/` — pytest testleri
- `scripts/` — PowerShell yardımcı scriptler
- `data/manual_import/` — CSV import deposu
