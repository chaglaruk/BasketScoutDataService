# BasketScout Real Price Test Matrix

Son guncelleme: 2026-05-13

Bu matris Milestone 26A yerel backend + Android testlerini tanimlar. Testler gercek zamanli fiyat/stok garantisi aramaz; sadece manuel/acik/sinirli veri gorunurlugunu ve mock fallback seffafligini dogrular.

## Backend test sepetleri

| Test | Sepet | Beklenen provider | Basari kriteri |
|---|---|---|---|
| B1 | milk + bread + eggs | manual_import | `/basket/compare` `metadata.data_mode` manuel/mixed; line item source manual_import; stock Unknown/null |
| B2 | bananas + pasta + rice | manual_import | En az bir qualifying store; line source manual_import; mock'a gereksiz dusmez |
| B3 | chicken breast + toilet roll | manual_import | Manual import fiyatlari doner; stock Unknown/null |
| B4 | unknown custom item | mock veya no-data fallback | `why_mock_used` veya warning mock/fallback nedenini aciklar |
| B5 | milk + bread + eggs, loyalty on | manual_import | Loyalty fiyati olan store line fiyatlari kullanilir; kazanan zorla degismez |

## Backend endpoint kontrolleri

| Endpoint | Kontrol | Basari kriteri |
|---|---|---|
| `GET /health` | Servis ayakta mi | `ok=true` |
| `GET /providers/status` | Mevcut provider durumu | mock, manual_import, open_prices, tesco gorunur |
| `GET /providers/reality` | Capability/reality raporu | price/stock/freshness/confidence alanlari var |
| `POST /basket/compare` | Sepet karsilastirma | metadata: provider_used, data_mode, confidence, freshness, warnings, why_mock_used |
| `GET /admin/provider-priority` | Provider sirasi | `manual_import > open_prices > tesco > mock` |

## Android testleri

| Test | Ekran/akis | Basari kriteri |
|---|---|---|
| A1 | Settings > Data Source | Local ADB / Remote / Offline mode gorunur |
| A2 | Settings > Remote URL validation | Invalid URL hata verir, app crash olmaz |
| A3 | Local backend + `adb reverse` | `milk + bread + eggs` manuel/acik/sinirli kaynak etiketi gosterir |
| A4 | Offline demo mode | Backend kullanmadan Offline demo prices etiketi ve sebebi gosterir |
| A5 | Result card | Price, source badge, freshness, confidence ve Stock: Unknown gorunur |
| A6 | Store Detail | Line source/confidence/freshness/stock alanlari okunur |
| A7 | Product Detail | Source, last checked, confidence, stock Unknown ve source URL gosterilir |
| A8 | Backend unavailable | Mock fallback sebebi aciklanir; crash yok |

## Zorunlu artifact'ler

- Backend response JSON:
  - `artifacts/real-price-<timestamp>/backend-milk-bread-eggs.json`
  - `artifacts/real-price-<timestamp>/backend-bananas-pasta-rice.json`
  - `artifacts/real-price-<timestamp>/backend-chicken-toilet-roll.json`
- Android:
  - Data source settings screenshot
  - Result section screenshot
  - Store Detail screenshot
  - Product Detail screenshot
  - Remote URL validation screenshot
  - Offline fallback screenshot
  - bounded `logcat.txt`

## Red/yellow/green karar

- GREEN: Manual/open/limited veri en az `milk + bread + eggs` icin Android'de gorunur; stok Unknown; crash yok.
- YELLOW: Backend calisir ama test sepetleri mock'a duser ve sebep UI'da aciktir.
- RED: Backend/Android crash, misleading live/stock iddiasi, veya source label yok.

---

## Milestone 26 local E2E results - 2026-05-13

| Basket | Backend artifact | Provider observed | Android evidence | Result |
|---|---|---|---|---|
| milk + bread + eggs | `artifacts/real-price-20260513-223630/milk-bread-eggs.json` | manual_import | `artifacts/phone-run-20260513-224241/home-result-section.png`, `store-detail-source.png`, `product-detail-data-expanded.png` | PASS |
| bananas + pasta + rice | `artifacts/real-price-20260513-223630/bananas-pasta-rice.json` | manual_import | backend response saved; app source path same as manual data mode | PASS |
| chicken breast + toilet roll | `artifacts/real-price-20260513-223630/chicken-toilet-roll.json` | manual_import | backend response saved; app source path same as manual data mode | PASS |
| Remote URL empty | n/a | n/a | `artifacts/phone-run-20260513-224241/settings-remote-url-validation.png` | PASS |
| Offline demo mode | n/a | mock fallback only | `artifacts/phone-run-20260513-224241/settings-offline-fallback.png` | PASS |

Crash check: `artifacts/phone-run-20260513-224241/logcat-final.txt` contains no crash indicators.
