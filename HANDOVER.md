# HANDOVER.md — El Teslimi Belgesi

Her anlamlı milestone sonrasında güncellenir.

---

## Son Güncelleme

Tarih: 2026-05-09
Milestone: 0–7 (Tam kurulum)

## Proje Durumu

**ÇALIŞIYOR** — Mock API tamamen işlevsel, testler geçiyor.

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
| 7 — Yerel Dev El Teslimi | ✅ | scripts/dev.ps1, test.ps1, smoke.ps1, doctor.ps1 |

## Çalışan Özellikler

- `GET /health` → Sağlık kontrolü
- `GET /providers/status` → 12 provider durumu (1 OK, 7 LIMITED, 4 OK/LIMITED)
- `GET /products/search?q=milk` → 10 ürün kategorisi mock verisi
- `GET /prices/latest?product=milk` → 8 perakendeci fiyatı
- `POST /basket/compare` → Tam sepet karşılaştırma, sıralama, öneriler
- `POST /admin/refresh` → Provider refresh tetikleme
- `GET /admin/runs` → Run geçmişi

## Provider Özeti

| Provider | Tip | Durum |
|---|---|---|
| mock | mock | ✅ OK |
| manual_import | manual | ✅ OK |
| open_food_facts | open_data | ✅ OK (internet gerekli) |
| open_prices | open_data | ~ LIMITED (barkod gerekli) |
| tesco | scraping | ~ LIMITED (JS/bot) |
| asda | scraping | ~ LIMITED (JS/bot) |
| sainsburys | scraping | ~ LIMITED (JS/bot) |
| morrisons | scraping | ~ LIMITED (JS/bot) |
| waitrose | scraping | ~ LIMITED (JS/bot) |
| coop | scraping | ~ LIMITED (JS/bot) |
| aldi | scraping | ~ LIMITED (JS/bot) |
| lidl | scraping | ~ LIMITED (JS/bot) |

## Tek Komutla Başlatma

```powershell
.\scripts\dev.ps1
```

## Sonraki Adımlar

1. Playwright + Tesco/Sainsbury's denemesi (bot koruma test edilmeli)
2. OpenPrices barkod entegrasyonu
3. PostgreSQL geçişi (ölçekleme için)
4. Admin token koruması
5. BasketScout Android entegrasyonu

## Bilinen Kısıtlamalar

- İngiltere süpermarketleri için garantili ücretsiz resmi API yok.
- Tüm scraping provider'ları JavaScript render / bot koruma nedeniyle LIMITED.
- Canlı fiyat verisi yalnızca scraping başarılı olduğunda mevcut.
- Mock veri gerçek fiyatları yansıtmaz — referans değerler.
