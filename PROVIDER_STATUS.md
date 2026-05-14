# PROVIDER_STATUS.md — Provider Durum Raporu

Son güncelleme: 2026-05-09

## Özet

| Provider | Tip | Durum | Açıklama |
|---|---|---|---|
| mock | mock | ✅ OK | Deterministik demo, her zaman çalışır |
| manual_import | manual | ✅ OK | CSV'den okur |
| open_food_facts | open_data | ✅ OK | Ürün meta verisi, internet gerekli |
| open_prices | open_data | ~ LIMITED | Barkod entegrasyonu gerekli |
| tesco | scraping | ~ LIMITED | JS render + bot koruma |
| asda | scraping | ~ LIMITED | JS render + bot koruma |
| sainsburys | scraping | ~ LIMITED | JS render + bot koruma |
| morrisons | scraping | ~ LIMITED | JS render + bot koruma |
| waitrose | scraping | ~ LIMITED | JS render + bot koruma |
| coop | scraping | ~ LIMITED | JS render + bot koruma |
| aldi | scraping | ~ LIMITED | JS render + bot koruma |
| lidl | scraping | ~ LIMITED | JS render + bot koruma |

## Retailer Provider Detayları

### Tesco — LIMITED

- Tesco.com arama, JavaScript ile render edilir.
- `https://www.tesco.com/groceries/en-GB/search?query=...` statik HTTP ile çalışmıyor.
- Bot koruma aktif (rate limiting, JS challenge).
- Çözüm: Playwright + stealth veya resmi API (şu an yok).

### Asda — LIMITED

- shop.asda.com dinamik React uygulaması.
- Statik HTTP sonuç vermiyor.
- Playwright gerekli.

### Sainsbury's — LIMITED

- sainsburys.co.uk arama API'si herkese açık değil.
- Statik HTML erişimi engellenmiş.

### Morrisons — LIMITED

- groceries.morrisons.com JavaScript render.
- Bot koruma sistemi aktif.

### Waitrose — LIMITED

- waitrose.com JavaScript SPA.
- Headless browser olmadan içerik yok.

### Co-op — LIMITED

- shop.coop.co.uk dinamik.
- Statik HTTP yetersiz.

### Aldi — LIMITED

- aldi.co.uk ürün sayfaları dinamik.
- "Aldi Finds" tarzı içerik düzensiz.

### Lidl — LIMITED

- lidl.co.uk GB ürün arama JavaScript.
- Statik erişim kısıtlı.

## Aktif Provider Öncelik Sırası (Milestone 28)

Fiyat karşılaştırması ve sepet optimizasyonu sırasında şu öncelik sırası uygulanır:

1. **manual_import** — En güvenilir, yönetici tarafından onaylanmış veri.
2. **open_prices** — Açık veri kaynağı (fiyat geçmişi).
3. **tesco** — Kısıtlı canlı kontrol (LIMITED).
4. **mock** — Fallback / Demo verisi.

Bu sıralama `GET /admin/provider-priority` endpoint'inden dinamik olarak kontrol edilebilir.

## Gelecek Geliştirme

1. Playwright entegrasyonu — JS render desteği
2. Tesco resmi API talebi izleme
3. Perakendeci RSS/sitemap beslemesi araştırması
4. Open Prices barkod entegrasyonu

---

## Milestone 26 provider reality update

Active priority remains:
1. `manual_import`
2. `open_prices`
3. `tesco_limited`
4. `mock`

Current status:
- `manual_import`: working for seeded common UK grocery test items; price yes; stock unknown; manually updated, not live.
- `open_food_facts`: working for metadata/barcode lookup; no price; no stock.
- `open_prices`: partial historical/crowdsourced prices; price partial; stock no.
- `tesco_limited`: limited confidence public-page probe only; no bypass/login/captcha; stock unknown.
- Asda, Sainsbury's, Aldi, Lidl, Morrisons, Waitrose, Co-op, Iceland, Ocado, M&S Food, Farmfoods: not safe/reliable for guaranteed live price/stock without official/licensed feed or manual/open data import.
- `mock`: fallback/demo only.

External blocker remains: guaranteed real-time price and stock across all retailers is not available from the current safe provider stack.

---

## Milestone 26C provider operations update - 2026-05-14

Changes:
- Manual import now has CSV validation, CSV import, CSV export, and an admin CLI/script wrapper.
- Sample manual CSV covers the common MVP products: milk, bread, eggs, bananas, pasta, rice, chicken breast, toilet roll.
- Manual rows carry `last_checked_at` and `confidence`; confidence defaults to `0.7` when omitted.
- Mock provider no longer advertises reliable stock. Mock price rows return `available = null`.
- OpenPrices remains partial. The provider safely uses OpenFoodFacts barcode candidates and GBP OpenPrices rows when clear enough, but sample `milk` returned no usable OpenPrices price in validation.
- Tesco remains limited. It uses only a low-volume public page probe, confidence `0.3`, no login/captcha/private API bypass, and no stock claim.

Current source capability:

| Provider | Price | Stock | Confidence | Notes |
|---|---|---|---:|---|
| manual_import | yes | no | 0.7 | manually updated CSV, preferred over mock |
| open_food_facts | no | no | n/a | metadata/barcodes only |
| open_prices | partial | no | 0.55-0.6 | open/crowdsourced/historical, sparse UK matches |
| tesco | partial | no | 0.3 | limited public-page probe only |
| mock | demo | no | n/a | fallback only |

Validation:
- Backend tests: 66 passed.
- Ruff: passed.
- Smoke: passed 5/5.
- Prod smoke: passed.

## Daily Web Observation Provider

- Provider name: `web_observation`
- Scope: only tracked watchlist URLs.
- Retailers currently modeled for adapter layer: Tesco, Aldi, Sainsbury's, Lidl.
- No crawling, no pagination, no link discovery.
- No login/captcha/WAF bypass.
- Stock is always `Unknown`.
- User-facing compare can use only `public_display_allowed=true` observations.

## Milestone 27D Controlled Observation Update (2026-05-14)

Exact URL seed adimi:

- 4 adet milk URL satiri eklendi (Tesco, Aldi, Sainsbury's, Lidl).
- Preflight sonucu nedeniyle yalnizca Aldi satiri enabled edildi.
- Tesco/Sainsbury's/Lidl satirlari policy blokaj notu ile disabled tutuldu.

Beklenen `/providers/status` daily observation alanlari:

- `enabled_watchlist_count`
- `enabled_url_count`
- `configured_url_count`
- `missing_url_count`
- `attempted_url_count`
- `observed_price_count`
- `blocked_by_policy_count`
- `blocked_by_access_count`
- `parse_failed_count`
- `internal_only_count`

Ilk real deneme sonucu:

- `urls_attempted=1` (Aldi)
- `prices_observed=0`
- `blocked_by_access=1`
- Stock: `Unknown`
- Public compare icin uygun web observation yok (`public_display_allowed=true` kayit yok).

## Milestone 27E Scrapling Lab Update (2026-05-14)

Yeni provider:

- `scrapling_observation` (safe lab mode)

Status ozeti:

- `scrapling_enabled`: config flag
- `scrapling_network_enabled`: config flag
- `scrapling_available`: parser runtime import durumu
- `scrapling_fetcher_available`, `scrapling_dynamic_fetcher_available`, `scrapling_stealthy_fetcher_available`: capability gorunurlugu
- `scrapling_last_run_at`, `scrapling_blocked_count`, `scrapling_parse_failed_count`, `scrapling_internal_only_count`, `scrapling_public_eligible_count`

Politika:

- No login/captcha/proxy/stealth bypass.
- No private API.
- Exact watchlist URL only.
- Stock her zaman `Unknown`.
