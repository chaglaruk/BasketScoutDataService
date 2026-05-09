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

## Gelecek Geliştirme

1. Playwright entegrasyonu — JS render desteği
2. Tesco resmi API talebi izleme
3. Perakendeci RSS/sitemap beslemesi araştırması
4. Open Prices barkod entegrasyonu
