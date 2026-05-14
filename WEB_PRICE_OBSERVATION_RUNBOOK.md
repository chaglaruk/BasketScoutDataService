# WEB_PRICE_OBSERVATION_RUNBOOK.md

Bu runbook gunluk web fiyat gozlem sisteminin operasyon adimlarini aciklar.

## 1. Lokal Calistirma

```powershell
python -m app.scripts.run_daily_price_observation --dry-run
```

Normal mod:

```powershell
python -m app.scripts.run_daily_price_observation
```

## 2. Watchlist Yonetimi

Watchlist goruntuleme:

- `GET /admin/web-watchlist`

Watchlist upsert:

- `POST /admin/web-watchlist/upsert`

Ornek body:

```json
{
  "retailer_slug": "tesco",
  "retailer_name": "Tesco",
  "canonical_product_name": "Semi-Skimmed Milk 2L",
  "product_url": "https://example.com/product",
  "expected_product_keywords": "milk,semi skimmed,2l",
  "enabled": true,
  "max_frequency_hours": 24,
  "policy_status": "allowed",
  "public_display_allowed": false,
  "notes": "Policy review pending"
}
```

## 3. Yeni Urun URL Ekleme Kurali

- URL gercek ve dogrudan urun URL'si olmali.
- URL repo disi tahmin edilmez, uydurulmaz.
- Policy/robots degerlendirmesi tamamlanmadan `public_display_allowed=true` yapmayin.

## 4. Retailer Devre Disi Birakma

- Ilgili satirda `enabled=false` yapin.
- Gerekceyi `notes` alanina yazin.

## 5. Son Calisma Kontrolu

- `GET /providers/status` icindeki daily observation alanlarini kontrol edin:
  - `daily_job_last_run_at`
  - `enabled_watchlist_count`
  - `successful_observations`
  - `blocked_count`
  - `parse_failed_count`
  - `internal_only_count`
  - `last_report_path`

## 6. Artifact ve Log Dosyalari

- Rapor: `artifacts/latest-price-observation-report.json`
- Log: `logs/latest-price-observation.log`

## 7. Beklenen Hata Tipleri

- `BLOCKED_BY_ROBOTS_OR_POLICY`
- `BLOCKED_BY_ACCESS_CONTROL`
- `PARSE_FAILED`
- `NETWORK_FAILED`

Bu hatalar job'u tumden dusurmez; script guvenli sekilde tamamlanir.

## 8. GitHub Actions Bildirim

Workflow: `.github/workflows/daily-price-observation.yml`

- Her gun UTC cron ile calisir.
- `workflow_dispatch` ile manuel tetiklenir.
- Uyari/hata varsa `BasketScout daily price observation needs attention` issue'su create/update edilir.
- Hatirlatma: Stock Unknown kalir, bypass denenmez.
