# HANDOVER.md — El Teslimi Belgesi

Her anlamlı milestone sonrasında güncellenir.

---

## Son Güncelleme

Tarih: 2026-05-09
Milestone: Tam Kurulum ve Son Audit

## Proje Durumu: WORKING

**ÇALIŞIYOR** — Tüm testler ve linter (Ruff) geçmektedir.

- **GitHub Repo URL:** https://github.com/chaglaruk/BasketScoutDataService
- **Güncel Commit Hash:** `bd0be06116ebc0920607c5930078d5bf7f963687`
- **Sunucu Durumu:** Çalışıyor (http://127.0.0.1:8787)
- **Endpoint Durumu (Smoke Test):** Başarılı (5/5)
  - `GET /health` (OK)
  - `GET /providers/status` (OK)
  - `GET /products/search?q=milk` (OK)
  - `GET /prices/latest?product=milk&postcode=SE13` (OK)
  - `POST /basket/compare` (OK)

## Tamamlanan Milestones

| Milestone | Durum | Açıklama |
|---|---|---|
| 0 — Proje Kurulumu | ✅ | Dizin yapısı, git, konfigürasyon |
| 1 — Mock API | ✅ | /health, /providers, /products, /prices, /basket |
| 2 — Provider Mimarisi | ✅ | BaseProvider, ProviderRegistry, cache politikası |
| 3 — Açık Veri Provider'ları | ✅ | OpenFoodFacts, OpenPrices iskelet |
| 4 — Scraping Spike | ✅ | 8 retailer iskelet, tümü LIMITED |
| 5 — Scheduler | ✅ | APScheduler, /admin/refresh, /admin/runs |
| 6 — Android Sözleşmesi | ✅ | API_CONTRACT.md, ANDROID_INTEGRATION_GUIDE.md |
| 7 — Yerel Dev El Teslimi | ✅ | scripts/dev.ps1, test.ps1, vb. |
| 8 — Final QA & Audit | ✅ | GitHub entegrasyonu, smoke test, linting |
| 9 — Real-data capability | ✅ | OpenPrices, Manuel Import scripti, Tesco safe probe |
| 10 — QA & Provider Hardening | ✅ | Safe probe kalitesi, sepet şeffaflığı, artifact'ler |

## Provider Özeti ve Veri Doğruluğu (Real vs Mock)

**ÖNEMLİ:** İngiltere süpermarketleri için garantili, ücretsiz, canlı API bulunmamaktadır. Sistemin canlı (gerçek) fiyat dönmediği, `mock` olarak çalıştığı açıkça belirtilmiştir.

| Provider | Tip | Durum | Veri Niteliği |
|---|---|---|---|
| mock | mock | ✅ OK | Sadece Mock/Demo verisi |
| manual_import | manual | ✅ OK | CSV'den statik fiyat verisi |
| open_food_facts | open_data | ✅ OK | Gerçek Açık Veri (Sadece meta veri, fiyat YOK) |
| open_prices | open_data | ~ LIMITED | Gerçek Açık Veri İskeleti (Barkod gerektiriyor) |
| tesco | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| asda | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| sainsburys | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| morrisons | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| waitrose | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| coop | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| aldi | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |
| lidl | scraping | ~ LIMITED | İskelet (JS/Bot Koruması) |

## Sonraki Önerilen Milestone

**Playwright & Headless Browser Entegrasyonu:**
Mevcut `ScrapingBaseProvider` iskeletlerinin, JS-rendered (React/SPA) ve bot korumalı süpermarket sayfalarını geçebilmesi için projeye `playwright` veya `selenium base` entegre edilerek (örneğin ilk olarak Tesco ve Sainsbury's üzerinde) gerçek zamanlı ağ taraması yeteneği kazandırılması.

## Milestone 26 Completed
Implemented provider priority (Manual > OpenPrices > Tesco > Mock). Enhanced API metadata with provider status summary and low-confidence counts.
