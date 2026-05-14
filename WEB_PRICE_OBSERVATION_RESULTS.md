# WEB_PRICE_OBSERVATION_RESULTS.md

Bu belge son daily web observation ciktilarini yorumlamak icin referanstir.

## Rapor Dosyasi

`artifacts/latest-price-observation-report.json`

Zorunlu alanlar:

- `started_at`
- `finished_at`
- `retailers_attempted`
- `urls_attempted`
- `prices_observed`
- `blocked_by_policy`
- `blocked_by_access`
- `parse_failed`
- `network_failed`
- `observations_published`
- `observations_internal_only`
- `warnings`
- `errors`

## Yorumlama

- `prices_observed > 0` tek basina guaranteed live price anlamina gelmez.
- `observations_published` sadece `public_display_allowed=true` satirlari kapsar.
- `observations_internal_only` kullanici-facing compare'e girmez.
- `blocked_*` degerleri beklenen guvenli davranistir; bypass denenmez.

## Stock Durumu

- Tum web observation kayitlarinda stock: `Unknown`.
- Uygulama stok var/yok iddiasi yapmaz.

## Aksiyon Rehberi

- `blocked_by_policy` artarsa URL/policy incelemesi yapin.
- `blocked_by_access` artarsa retailer erisim kisitina saygi gosterin, bypass denemeyin.
- `parse_failed` artarsa parser'i guvenli regex seviyesinde iyilestirin.
- `network_failed` artarsa timeout/erisim kosullarini kontrol edin.
