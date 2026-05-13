# BasketScout Real Price Provider Audit

Son guncelleme: 2026-05-13

Bu dokuman Milestone 26A icin fiyat/stok kaynaklarinin gercek durumunu aciklar. Amac, uygulamanin hangi veriyi neden gosterdigini dürüstce etiketlemek ve “canli fiyat / kesin stok” iddiasi yapmamaktir.

## Audit ilkeleri

- Provider onceligi: `manual_import > open_prices > tesco_limited > mock`.
- Mock fallback korunur; ancak manuel/acik/sinirli veri varsa kullaniciya net sekilde gosterilir.
- Stok durumu sadece provider guvenilir sekilde dogruluyorsa “confirmed” olabilir. Aksi halde `Unknown`.
- Captcha, login, paywall, bot koruma veya private app API bypass edilmez.
- Agresif scraping yapilmaz.
- Open Food Facts belgeleri, READ isteklerinde custom User-Agent ister ve search endpointleri icin rate limit uygular. Bu nedenle search-as-you-type veya yogun tarama yapilmaz.
- Open Prices, Open Food Facts ekosisteminde fiyat toplamak/paylasmak icin acik REST API sunan crowdsourced bir projedir; resmi supermarket fiyati veya stok garantisi degildir.

## Kaynak/store gerçeklik tablosu

| Kaynak / Store | Mevcut implementasyon | Fiyat verebilir mi? | Stok verebilir mi? | Tazelik | Guven | Login/session gerekir mi? | Hukuki/guvenlik siniri | Blok/limit nedeni | Sonraki guvenli adim |
|---|---|---:|---:|---|---|---:|---|---|---|
| Manual import | `ManualImportProvider`, CSV tabanli | Evet | Hayir, varsayilan Unknown | CSV `last_checked_at` veya yukleme zamani | Orta | Hayir | Manuel veri; canli degil | Stok dogrulama yok | CSV alanlarini `source`, `last_checked_at`, confidence ile guclendir |
| OpenFoodFacts | `OpenFoodFactsProvider`, metadata/barcode | Hayir | Hayir | Crowdsourced metadata | Orta | READ icin hayir, User-Agent gerekli | Rate limit ve ODbL/DBCL/CC BY-SA lisanslari | Fiyat/stok vermez | Barcode/metadata eslestirmeyi OpenPrices icin yardimci kullan |
| OpenPrices | `OpenPricesProvider` | Kismi | Hayir | Crowdsourced/historical | Dusuk-Orta | Hayir | Open/crowdsourced; resmi retailer fiyati degil | UK kapsami ve urun/store eslesmesi sinirli | Barcode + currency + store mapping filtrelerini sertlestir |
| Tesco | `TescoProvider`, safe low-confidence probe | Kismi | Hayir | Anlik HTTP probe olabilir ama guven dusuk | Dusuk | Hayir | Bot koruma/captcha/login bypass yok | Dinamik sayfa, regex heuristic | Resmi/public API varsa kullan; aksi halde limited kal |
| Asda | Limited provider, fiyat cekmiyor | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Statik HTTP guvenilir degil | Sadece resmi/acik kaynak bulunursa ekle |
| Sainsbury's | Limited provider, fiyat cekmiyor | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Statik HTML/API herkese acik degil | Resmi/acik veri bekle veya manuel import |
| Aldi | Limited provider, fiyat cekmiyor | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Dinamik/bot korumali | Resmi/acik veri bekle veya manuel import |
| Lidl | Limited provider, fiyat cekmiyor | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Dinamik arama | Resmi/acik veri bekle veya manuel import |
| Morrisons | Limited provider, fiyat cekmiyor | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | JS render/bot koruma | Resmi/acik veri bekle veya manuel import |
| Waitrose | Limited provider, fiyat cekmiyor | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | JS render | Resmi/acik veri bekle veya manuel import |
| Co-op | Limited provider, fiyat cekmiyor | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Statik HTTP yetersiz | Resmi/acik veri bekle veya manuel import |
| Iceland | Android loyalty list mevcut; backend provider yok | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Implementasyon yok | Provider ekleme oncesi resmi/acik veri arastir |
| Ocado | Backend provider yok | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Implementasyon yok | Provider ekleme oncesi resmi/acik veri arastir |
| M&S Food | Backend provider yok | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Implementasyon yok | Provider ekleme oncesi resmi/acik veri arastir |
| Farmfoods | Backend provider yok | Hayir | Hayir | Yok | Dusuk | Belirsiz | Bot koruma/private API bypass yok | Implementasyon yok | Provider ekleme oncesi resmi/acik veri arastir |
| Mock | `MockProvider` | Evet, demo | Demo-only; gerçek stok degil | Statik | Deterministik demo | Hayir | Gercek fiyat/stok degil | Fallback amacli | Sadece backend verisi yoksa kullan |

## Örnek ürün görünürlüğü hedefi

Hedef ürünler:

- milk
- bread
- eggs
- bananas
- pasta
- rice
- chicken breast
- toilet roll

Beklenen yerel sonuc:

- `milk + bread + eggs`: manual import fiyatlari donmeli.
- `bananas + pasta + rice`: manual import fiyatlari donmeli.
- `chicken breast + toilet roll`: manual import fiyatlari donmeli.
- Manual import kapsamadigi satirlarda OpenPrices/Tesco denenebilir; onlar da veri vermezse mock fallback sebebi aciklanmali.

## Kaynaklar

- Open Food Facts API dokumani: custom User-Agent, rate limit ve veri guvenilirligi uyarilari.
- Open Prices dokumani: Open Prices REST API ve crowdsourced fiyat toplama amaci.
- Mevcut repo kaynaklari: `app/providers/*`, `app/services/provider_registry.py`, `data/manual_import/sample_prices.csv`.

---

## Milestone 26 validation addendum - 2026-05-13

Validated local provider behavior:
- `milk + bread + eggs`: `manual_import`, winner Aldi, 100% coverage for direct API sample, stock Unknown.
- `bananas + pasta + rice`: `manual_import`, winner Aldi, 100% coverage for direct API sample, stock Unknown.
- `chicken breast + toilet roll`: `manual_import`, winner Aldi, 100% coverage for direct API sample, stock Unknown.

Manual import is now the only source used for these sample baskets because seeded manual rows cover the requested aliases. OpenPrices and Tesco remain fallback/partial paths, not guaranteed live sources.

Safety decision remains unchanged: no captcha/login/paywall/private API bypass; no claim of guaranteed stock.
