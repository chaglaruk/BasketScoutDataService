# API_CONTRACT.md — API Sözleşmesi

BasketScout Android uygulaması ile BasketScoutDataService arasındaki
API sözleşmesi.

**Temel URL:** `http://127.0.0.1:8787` (yerel) / yapılandırılabilir

---

## GET /health

**Amaç:** Servis sağlık kontrolü.

**Yanıt:**
```json
{
  "ok": true,
  "service": "BasketScoutDataService",
  "version": "0.1.0",
  "time": "2026-05-09T00:00:00Z",
  "env": "development"
}
```

---

## GET /providers/status

**Amaç:** Tüm provider'ların durumunu döndürür.

**Yanıt:**
```json
{
  "providers": [
    {
      "name": "mock",
      "status": "ok",
      "type": "mock",
      "last_run_at": "2026-05-09T00:00:00Z",
      "message": "Mock provider aktif.",
      "limitations": ["Demo verisi — gerçek fiyatları yansıtmaz."],
      "supports_live_prices": false,
      "supports_stock": true,
      "requires_postcode": false
    }
  ]
}
```

**Provider durum değerleri:** `ok | limited | blocked | error | unknown`

---

## GET /products/search

**Parametreler:**
- `q` (zorunlu) — arama terimi
- `provider` (opsiyonel) — belirli provider adı

**Örnek:** `GET /products/search?q=milk`

**Yanıt:**
```json
{
  "query": "milk",
  "items": [
    {
      "id": 1,
      "canonical_name": "Semi-Skimmed Milk 2L",
      "category": "Dairy",
      "brand": null,
      "aliases": ["milk", "semi skimmed milk", "2l milk"],
      "source": "mock",
      "confidence": 1.0
    }
  ],
  "count": 1
}
```

---

## GET /prices/latest

**Parametreler:**
- `product` (zorunlu) — ürün adı
- `postcode` (opsiyonel) — posta kodu
- `provider` (opsiyonel) — belirli provider

**Örnek:** `GET /prices/latest?product=milk&postcode=SE13`

**Yanıt:**
```json
{
  "query": "milk",
  "postcode": "SE13",
  "items": [
    {
      "retailer": "Tesco",
      "retailer_slug": "tesco",
      "product": "Semi-Skimmed Milk 2L",
      "price": 1.55,
      "currency": "GBP",
      "unit_price": null,
      "unit_price_unit": null,
      "loyalty_price": 1.40,
      "own_brand": false,
      "available": true,
      "raw_availability_text": null,
      "source": "mock",
      "source_url": null,
      "last_checked_at": "2026-05-09T00:00:00Z",
      "confidence": 1.0,
      "is_stale": false
    }
  ],
  "count": 8,
  "any_stale": false,
  "warning": null
}
```

---

## POST /basket/compare

**İstek:**
```json
{
  "postcode": "SE13",
  "coverage_threshold": 0.9,
  "use_loyalty_prices": true,
  "allow_own_brand": true,
  "items": [
    {"name": "milk", "quantity": 1},
    {"name": "bread", "quantity": 2},
    {"name": "eggs", "quantity": 1}
  ]
}
```

**Yanıt:**
```json
{
  "recommended": {
    "retailer": "Aldi",
    "total_price": 2.97,
    "coverage": 1.0,
    "matched_count": 3,
    "requested_count": 3,
    "missing_items": [],
    "savings_vs_priciest": 2.08
  },
  "stores": [
    {
      "retailer": "Aldi",
      "retailer_slug": "aldi",
      "qualifies": true,
      "total_price": 2.97,
      "coverage": 1.0,
      "matched_count": 3,
      "missing_items": [],
      "line_items": [
        {
          "requested_name": "milk",
          "canonical_name": "Semi-Skimmed Milk 2L",
          "quantity": 1,
          "unit_price": 1.29,
          "line_total": 1.29,
          "available": true,
          "source": "mock",
          "source_url": null,
          "last_checked_at": "2026-05-09T00:00:00Z",
          "confidence": 1.0,
          "is_stale": false
        }
      ]
    }
  ],
  "metadata": {
    "data_mode": "mock",
    "generated_at": "2026-05-09T00:00:00Z",
    "warnings": []
  }
}
```

---

## POST /admin/refresh

> Admin endpoint'leri için `X-Admin-Token` header'ı gerekebilir.
> `ENV=production` ve `ADMIN_TOKEN` yoksa admin endpoint'leri `503` döner.
> `ADMIN_TOKEN` ayarlıysa eksik/yanlış token `401` döner.

**İstek (opsiyonel):**
```json
{
  "provider": "mock",
  "product_names": ["milk", "bread"]
}
```

**Yanıt:**
```json
{
  "triggered_at": "2026-05-09T00:00:00Z",
  "results": [
    {
      "provider": "mock",
      "status": "ok",
      "message": "Mock veri zaten güncel."
    }
  ]
}
```

---

---

## GET /admin/manual-prices

**Amaç:** Tüm manuel fiyat kayıtlarını listeler.

**Yanıt:** `list[ManualPriceImportItem]`

---

## POST /admin/manual-prices/import

**Amaç:** Yeni manuel fiyat kayıtlarını içe aktarır.

**İstek:** `list[ManualPriceImportItem]`

**Yanıt:**
```json
{
  "rows_imported": 10,
  "rows_skipped": 0,
  "validation_errors": [],
  "duplicate_handling": "overwrite"
}
```

---

## GET /admin/manual-prices/template

**Amaç:** CSV şablonu döndürür.

---

## GET /admin/provider-priority

**Amaç:** Aktif provider öncelik sırasını döndürür.

**Yanıt:**
```json
{
  "priority_order": ["manual_import", "open_prices", "tesco", "mock"],
  "description": "..."
}
```

---

## GET /admin/runs

**Yanıt:**
```json
{
  "runs": [
    {
      "triggered_at": "2026-05-09T00:00:00Z",
      "provider": "all",
      "results": [...]
    }
  ]
}
```

---

## Hata Yanıtları

```json
{
  "detail": "Arama terimi boş olamaz."
}
```

HTTP durum kodları:
- 200 — Başarılı
- 400 — Geçersiz istek
- 404 — Bulunamadı
- 503 — Servis kullanılamıyor

---

## Önemli Notlar

1. Her fiyat yanıtı `source`, `confidence`, `last_checked_at`, `is_stale` içerir.
2. `data_mode: "mock"` → gerçek fiyat değil.
3. `is_stale: true` → TTL aşıldı, veri güncel olmayabilir.
4. `confidence < 1.0` → veri doğruluğu garanti değil.
5. `available: null` → stok bilgisi mevcut değil.

---

## Milestone 26 metadata additions

`POST /basket/compare` now includes these metadata fields for Android source transparency:

```json
{
  "provider_used": "manual_import",
  "data_mode": "manual data",
  "confidence": "medium",
  "last_checked_at": "2026-05-13T21:36:16Z",
  "freshness": "fresh",
  "why_mock_used": null,
  "stock_status": "Unknown unless provider confirms reliable availability",
  "line_source_summary": { "manual_import": 17 },
  "warnings": []
}
```

Rules:
- `why_mock_used` is present when mock fallback is used.
- `stock_status` must not claim in-stock unless a provider confirms reliable availability.
- Mixed provider baskets use `data_mode = mixed` and line-level source counts.

New endpoint:

`GET /providers/reality`

Returns provider capability rows for manual import, OpenFoodFacts, OpenPrices, Tesco limited, mock fallback, and currently blocked/limited retailers. Use this for diagnostics and deployment readiness, not as a consumer shopping API.

---

## Milestone 26C manual feed operations

New manual CSV endpoints:

| Method | Path | Body | Result |
|---|---|---|---|
| `POST` | `/admin/manual-prices/validate-csv` | raw `text/csv` | `ManualCsvValidationReport`, no data mutation |
| `POST` | `/admin/manual-prices/import-csv` | raw `text/csv` | imports valid rows, skips invalid rows, reloads manual provider |
| `GET` | `/admin/manual-prices/export` | none | current manual feed as `text/csv` |

`ManualCsvValidationReport` fields:

```json
{
  "total_rows": 37,
  "valid_rows": 37,
  "invalid_rows": 0,
  "duplicate_rows": 0,
  "missing_required_fields": 0,
  "stale_rows": 0,
  "issues": [],
  "duplicate_handling": "last row wins"
}
```

`ManualImportSummary` now includes `total_rows`, `duplicate_rows`, `invalid_rows`, `missing_required_fields`, and `stale_rows` in addition to imported/skipped counts.

`GET /prices/latest?product=<name>&provider=<provider>` now returns a plain `warning` when a specific provider returns zero rows. This is used for OpenPrices/Tesco limited fallback clarity and does not force mock fallback when the caller explicitly asks for one provider.

Stock rule remains unchanged: `available: null` means stock is unknown. Do not interpret manual/mock/open price rows as confirmed stock.

---

## GET /providers/status (Daily Observation Fields)

Response now includes:

- `daily_job_last_run_at`
- `enabled_watchlist_count`
- `successful_observations`
- `blocked_count`
- `parse_failed_count`
- `internal_only_count`
- `last_report_path`
- `last_issue_url`

---

## GET /admin/web-watchlist

Returns configured web observation watchlist rows.

## POST /admin/web-watchlist/upsert

Creates/updates a watchlist row.

## POST /admin/daily-observation/run

Runs daily observation manually.

Request:

```json
{
  "dry_run": true,
  "force": false
}
```

---

## Daily Observation Script Output

`python -m app.scripts.run_daily_price_observation` writes:

- `artifacts/latest-price-observation-report.json`
- `logs/latest-price-observation.log`

Important:

- Observed web price is not guaranteed live price.
- Stock remains `Unknown`.
