# MANUAL_PRICE_FEED.md

## Amac

Manual price feed, BasketScout icin guvenli ve bakimi kolay fiyat giris yoludur. Bu veri canli supermarket API'si degildir; fiyatlar dosya veya admin import ile elle guncellenir ve uygulamada "Manually updated price data" olarak etiketlenir.

## Kaynak dosya

Varsayilan CSV:

`data/manual_import/sample_prices.csv`

Zorunlu alanlar:

| Alan | Aciklama |
|---|---|
| `retailer` | Kullaniciya gorunen market adi |
| `retailer_slug` | Stabil market anahtari, ornek `tesco` |
| `product_name` | Canonical urun adi |
| `price` | GBP fiyat, `> 0` olmali |

Opsiyonel alanlar:

| Alan | Aciklama |
|---|---|
| `alias` | Eslesme icin kullanilan kisa ad |
| `category` | Dairy, bakery, pantry gibi kategori |
| `loyalty_price` | Varsa uye fiyati |
| `available` | Bos birakilmali, guvenilir stok yoksa `Unknown` |
| `postcode` | Bolgesel veri icin opsiyonel alan |
| `source_url` | Kaynak sayfa veya operator notu |
| `last_checked_at` | ISO-8601 kontrol zamani |
| `confidence` | `0.0` - `1.0`; manual feed icin varsayilan `0.7` |

## Admin endpointleri

| Endpoint | Amac |
|---|---|
| `GET /admin/manual-prices` | Mevcut manual satirlari listeler |
| `POST /admin/manual-prices/import` | JSON liste import eder |
| `GET /admin/manual-prices/template` | CSV sablonu dondurur |
| `POST /admin/manual-prices/validate-csv` | CSV'yi kaydetmeden dogrular |
| `POST /admin/manual-prices/import-csv` | Gecerli CSV satirlarini import eder |
| `GET /admin/manual-prices/export` | Mevcut manual feed'i CSV olarak export eder |

Production ortaminda admin endpointleri `ADMIN_TOKEN` ile korunmalidir.

## CLI / script kullanimi

PowerShell wrapper:

```powershell
.\scripts\manual_feed.ps1 -Command validate -Path data\manual_import\sample_prices.csv
.\scripts\manual_feed.ps1 -Command import -Path data\manual_import\sample_prices.csv
.\scripts\manual_feed.ps1 -Command export -Path artifacts\manual-export.csv
.\scripts\manual_feed.ps1 -Command summary
```

Python modul:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.import_csv validate data\manual_import\sample_prices.csv
.\.venv\Scripts\python.exe -m app.scripts.import_csv import data\manual_import\sample_prices.csv
.\.venv\Scripts\python.exe -m app.scripts.import_csv export artifacts\manual-export.csv
.\.venv\Scripts\python.exe -m app.scripts.import_csv summary
```

## Validation report

CSV validation raporu su alanlari dondurur:

| Alan | Anlam |
|---|---|
| `total_rows` | Header haric toplam satir |
| `valid_rows` | Import edilebilir satir sayisi |
| `invalid_rows` | Reddedilen satir sayisi |
| `duplicate_rows` | Ayni `(retailer_slug, product_name, postcode)` anahtarina sahip tekrarlar |
| `missing_required_fields` | Zorunlu alan eksikleri |
| `stale_rows` | 30 gunden eski veya tarihi eksik satirlar |
| `issues` | Satir/alan bazli hata veya uyari listesi |

Duplicate davranisi: son satir kazanir.

## Mevcut sample kapsam

`data/manual_import/sample_prices.csv` su hedef urunleri kapsar:

- milk
- bread
- eggs
- bananas
- pasta
- rice
- chicken breast
- toilet roll

Mevcut sample feed 37 satirdir ve su marketleri kapsar:

- Tesco
- Asda
- Sainsbury's
- Morrisons
- Waitrose
- Aldi
- Lidl

## Stok politikasi

Manual feed guvenilir stok kanali degildir. `available` bos birakildiginda backend ve Android stok durumunu `Unknown` gosterir. Stok bilgisi yalnizca guvenilir, provider tarafindan dogrulanmis bir kaynakla gelirse "available" gibi yorumlanabilir.

## Milestone 26C validation

2026-05-14 sonuc:

- `validate sample_prices.csv`: 37 total, 37 valid, 0 invalid, 0 duplicate, 0 stale.
- Backend tests: 66 passed.
- Ruff lint: passed.
- Smoke: 5/5 passed.
- Prod smoke: passed.
- Android Local ADB mode: phone screenshotlarda "Manually updated price data" gorundu.
