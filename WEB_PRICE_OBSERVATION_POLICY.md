# WEB_PRICE_OBSERVATION_POLICY.md

Bu belge BasketScout gunluk web fiyat gozlem politikasini tanimlar.

## Kapsam

- Hedef: Takip edilen urunler icin gunluk fiyat gozlemi.
- Kapsam disi: Tum katalog tarama, kategori spider, link discovery.

## Kesin Kurallar

- Sadece `web_price_watchlist` tablosundaki **enabled** satirlar denenir.
- Sadece satirdaki `product_url` kullanilir.
- Arama sayfasi pagination, auto-discovery, crawl zinciri yoktur.
- Login/captcha/WAF/private API bypass kesinlikle yoktur.
- Proxy rotation yoktur.
- Checkout/add-to-cart otomasyonu yoktur.
- Her URL en fazla `max_frequency_hours` araliginda bir kez denenir (varsayilan 24 saat).

## Politika ve Robots

- robots/policy preflight calisir.
- Disallow veya policy riski varsa sonuc `BLOCKED_BY_ROBOTS_OR_POLICY` olur.
- Erisim engeli (403/captcha/challenge) varsa `BLOCKED_BY_ACCESS_CONTROL` olur.

## Veri Dogrulugu

- Bu veri "guaranteed live" degildir.
- Kaynak etiketi: `Observed web price`.
- Uyarý: "Observed from public web page. Price may change."
- `stock_status` her zaman `Unknown` kalir.

## Public Gosterim Kurali

- `public_display_allowed=false` olan gozlemler kullanici-facing compare'e girmez.
- Bu gozlemler sadece internal/admin amacli kalir.

## Guvenli Escalation

- Bloklanan retailer icin bypass denenmez.
- Blok/parse/policy olaylari raporlanir.
- GitHub Actions issue mekanizmasi ile dikkat gerektiren durum bildirilir.
