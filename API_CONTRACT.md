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
