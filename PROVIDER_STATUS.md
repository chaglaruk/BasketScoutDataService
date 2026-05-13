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
