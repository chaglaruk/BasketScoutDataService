# ARCHITECTURE.md — Teknik Mimari

## Genel Bakış

```
Android Uygulaması
        │  HTTP/JSON
        ▼
┌─────────────────────────────────────────┐
│         FastAPI (Uvicorn, :8787)        │
│  /health  /products  /prices  /basket   │
│  /providers/status  /admin/refresh      │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼────────┐
        │ ProviderRegistry│  ← tüm provider'ları yönetir
        └────────┬────────┘
                 │
    ┌────────────┼────────────────────────┐
    │            │                        │
    ▼            ▼                        ▼
MockProvider  ManualImport         OpenFoodFacts
(her zaman)   (CSV)                (meta veri)
                                         │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                      Tesco(L)      Asda(L)       Aldi(L)  ...
                      [LIMITED]    [LIMITED]     [LIMITED]

    ProviderRegistry
        │
        ▼
    Services
    ├── ProductService   → search, deduplicate
    ├── PriceService     → fetch, annotate staleness
    ├── BasketService    → compare, rank, recommend
    ├── RefreshService   → trigger provider refresh
    └── CachePolicy      → TTL, staleness, data_mode

    Services
        │
        ▼
    SQLAlchemy ORM
        │
        ▼
    SQLite (data/basketscout.db)
```

## Veri Katmanları

### 1. Veritabanı Modelleri (`app/db/models.py`)

- `Retailer` — perakendeci bilgisi
- `Product` — normalize edilmiş ürün kaydı
- `ProductAlias` — ürün isim takma adları
- `StoreLocation` — mağaza konum (opsiyonel)
- `PriceSnapshot` — zaman damgalı fiyat kaydı
- `AvailabilitySnapshot` — stok durumu
- `ProviderRun` — provider çalıştırma geçmişi

### 2. Domain Modelleri (`app/domain/models.py`)

Pydantic v2 şemaları — API'de kullanılan veri yapıları.

### 3. Provider Katmanı (`app/providers/`)

Her provider `BaseProvider` ABC'yi uygular:
- `status()` → `ProviderStatusItem`
- `search_products(query)` → `list[ProductSummary]`
- `get_latest_prices(names, postcode)` → `list[PriceItem]`

### 4. Servis Katmanı (`app/services/`)

- Provider hatalarını izole eder
- Cache politikası uygular
- İş kurallarını uygular

### 5. API Katmanı (`app/api/`)

FastAPI route'ları — yalnızca HTTP şeması, iş mantığı yok.

## Güven Skoru Modeli

| Kaynak | Güven Tavanı |
|---|---|
| mock | 1.0 |
| manual_import | 0.7 |
| scraping (taze) | 0.9 |
| scraping (eski) | azalan |
| crowdsourced | 0.6 |

## Cache / Tazelik

- Fiyat TTL: 6 saat (yapılandırılabilir)
- Stok TTL: 1 saat (yapılandırılabilir)
- Eski veri `is_stale: true` ile döner
- Yanıt `data_mode`: mock | live | cache | mixed

## Ölçekleme Yolu

MVP: SQLite + tek process
→ PostgreSQL + bağlantı havuzu
→ Redis cache
→ Ayrı scraping worker process
→ Kubernetes (ileride)
