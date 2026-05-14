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

## Milestone 27D - Ilk Controlled Exact-URL Denemesi (2026-05-14)

Seed edilen exact URL satirlari:

- Tesco milk: `https://www.tesco.com/shop/en-GB/products/252207566`
- Aldi milk: `https://www.aldi.co.uk/product/cowbelle-semi-skimmed-milk-1-7-fat-000000000000416770`
- Sainsbury's milk: `https://www.sainsburys.co.uk/gol-ui/product/sainsburys-british-whole-milk-2-27l-4-pint`
- Lidl milk: `https://www.lidl.co.uk/p/milbona-uht-skimmed-milk/p10000029`

Preflight sonucu:

- Tesco: `blocked_by_policy` (robots fetch 403)
- Aldi: `allowed`
- Sainsbury's: `blocked_by_policy` (robots fetch 403)
- Lidl: `blocked_by_policy` (robots fetch SSL verification error)

Calisma sonucu:

- Dry-run: `urls_attempted=1`, `prices_observed=0`, hata yok.
- Real-run: `urls_attempted=1`, `prices_observed=0`, `blocked_by_access=1` (Aldi sayfa iceriginde access-control marker).
- `public_display_allowed=true` satir yok; kullanici-facing compare'e yayinlanan web observation yok.

## Milestone 27E - Scrapling Lab Controlled Run (2026-05-14)

- `--provider scrapling --dry-run --force` (SCRAPLING_ENABLED=false):
  - `urls_attempted=0`, warning: provider disabled.
- `--provider scrapling --dry-run --force` (SCRAPLING_ENABLED=true):
  - `urls_attempted=1`, network call yok (dry-run).
- `--provider scrapling --force` (SCRAPLING_ENABLED=true):
  - `urls_attempted=1`
  - `prices_observed=0`
  - `blocked_by_access=1` (Aldi URL access-control marker)
  - `public_eligible=0`

Not:
- Fetcher/Dynamic/Stealthy capability runtime'da tespit edilir; bu milestone'da bypass amacli kullanilmamistir.
