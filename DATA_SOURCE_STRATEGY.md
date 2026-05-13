# DATA_SOURCE_STRATEGY.md — Veri Kaynağı Stratejisi

## Temel Gerçek

> **İngiltere süpermarketleri için garantili, ücretsiz, resmi, canlı fiyat + stok API'si yoktur.**

Bu belge, bu kısıtlama altında nasıl çalışıldığını açıklar.

---

## Mevcut Veri Kaynakları

### 1. Open Food Facts (`open_food_facts`)

**Ne sunar:** Ürün meta verisi — barkod, kategori, marka, besin değerleri.
**Fiyat sunar mı:** HAYIR.
**Stok sunar mı:** HAYIR.
**Kullanım amacı:** Ürün tanımlama, normalleştirme yardımcısı.
**URL:** https://world.openfoodfacts.org
**Lisans:** ODbL — açık veri.
**Güven:** 0.7 (kitlesel kaynak, doğrulama yok).

### 2. Open Prices (`open_prices`)

**Ne sunar:** Kullanıcı tarafından girilen fiyat verileri.
**Canlı fiyat mı:** HAYIR — kitlesel kaynaklı, gecikmeli.
**Stok sunar mı:** HAYIR.
**Kullanım amacı:** Fiyat ipucu, doğrulama yardımcısı.
**URL:** https://prices.openfoodfacts.org
**Güven tavanı:** 0.6 (kullanıcı girişi, hata olabilir).
**MVP durumu:** Barkod entegrasyonu gerektiğinden iskelet.

### 3. Mock Provider (`mock`)

**Ne sunar:** Deterministik demo verisi — 10 ürün, 8 perakendeci.
**Amaç:** Geliştirme, test, Android entegrasyon demo.
**Canlı veri mi:** HAYIR — statik referans değerleri.
**Güven:** 1.0 (demo veri olduğu bilindiğinden).

### 4. Manual Import Provider (`manual_import`)

**Ne sunar:** CSV dosyasından okunan fiyatlar.
**Amaç:** Manuel veri yedek, scraping başarısız olduğunda.
**CSV yolu:** `data/manual_import/sample_prices.csv`
**Güven:** 0.7 (manuel veri, doğrulanamaz).

### 5. Retailer Scraping (Tesco, Asda, vb.)

**Durum:** Tüm perakendeciler şu anda **LIMITED**.
**Neden:**
- Arama sayfaları JavaScript ile render edilir (statik HTTP yetersiz).
- Bot koruma sistemleri aktif.
- Playwright entegrasyonu henüz eklenmedi.

**Politika:**
- Captcha bypass yapılmaz.
- Login gerektiren sayfalara erişilmez.
- robots.txt'e saygı gösterilir.
- Rate limit uygulanır (>2 saniye arası).

---

## Cache ve Tazelik Modeli

| Veri Tipi | TTL | Stale Davranış |
|---|---|---|
| Fiyat | 6 saat | `is_stale: true` ile döner |
| Stok | 1 saat | `is_stale: true` ile döner |

Eski veri yerine sıfır veri döndürülmez.
Android uygulaması `is_stale` ve `confidence` değerlerini kullanarak
kullanıcıya uyarı gösterebilir.

---

## Güven Skoru Modeli

```
1.0  → Mock (demo)
0.9  → Taze live scraping
0.7  → Manual import / Open Food Facts
0.6  → Crowdsourced (Open Prices)
azalan → Eski veri (TTL aşıldıkça düşer)
```

---

## Yasal ve ToS Güvenliği

- Yalnızca herkese açık sayfalar ziyaret edilir.
- Giriş, captcha veya ödeme duvarı gerektiren içeriğe erişilmez.
- robots.txt'e uyulur.
- İstekler arasında minimum 2 saniye beklenir.
- Kullanıcı ajanı şeffaf şekilde tanımlanır.
- Bir perakendeci erişimi engellerse: LIMITED/BLOCKED olarak işaretlenir,
  durdurulur ve belgelenir.

---

## Provider Durum Modeli

| Durum | Anlamı |
|---|---|
| ok | Provider çalışıyor, veri alınıyor |
| limited | Kısmi erişim (örn. JS render gerekiyor) |
| blocked | Erişim engellendi (bot koruması, captcha) |
| error | Beklenmedik hata |
| unknown | Henüz test edilmedi |

---

## Milestone 26 data-source strategy

Provider selection must prefer real/manual/open/limited data before mock:
`manual_import > open_prices > tesco_limited > mock`.

Implementation rules:
- Do not query mock for product names that are already covered by non-mock providers.
- If mock is used, include `why_mock_used` in `/basket/compare` metadata.
- Label manual data as manually updated, not live.
- Label OpenPrices as open/crowdsourced/historical.
- Label Tesco as limited-confidence.
- Stock remains Unknown unless explicitly confirmed by a reliable provider.
- Do not bypass captcha, login, paywall, private APIs, or bot protection.

Safe next step for broader coverage:
- Add admin/manual import tooling for more current retailer CSV feeds.
- Investigate official/licensed data partners before attempting retailer automation.
- Improve OpenPrices barcode matching only where product/store/currency mapping is clear enough to avoid misleading prices.
