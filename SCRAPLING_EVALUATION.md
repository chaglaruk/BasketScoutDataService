# SCRAPLING_EVALUATION.md

Bu belge BasketScoutDataService icin Scrapling denemesinin teknik degerlendirmesidir.

## Hedef

- Gunluk web observation pipeline'inda parser kirilganligini azaltmak.
- Exact URL watchlist modelini koruyarak kontrollu calisma saglamak.
- Sonuclari varsayilan olarak internal-only tutmak.

## BasketScout icin degerli Scrapling ozellikleri

1. `Selector` parser:
- CSS/XPath seciciler ile urun basligi/fiyat parcasi cikarma.
- `adaptive=True` ile DOM degisimlerinde secici dayanikliligini artirma.

2. Fixture tabanli parse:
- Kaydedilmis minimal HTML fixture'lari ag bagimsiz parse etmek.
- Parser davranisini testlerde deterministik hale getirmek.

3. Fetcher siniflari (opsiyonel):
- `Fetcher`: HTTP tabanli get/fetch akisi.
- `DynamicFetcher`: browser tabanli dinamik render.
- `StealthyFetcher`: anti-bot bypass odakli mod.

Not:
- Bu projede bypass politikasina aykiri oldugu icin `DynamicFetcher` ve `StealthyFetcher` kullanimi acik degildir.
- Runtime'da varliklari sadece capability olarak raporlanir.

## Fetcher vs DynamicFetcher vs StealthyFetcher (BasketScout karari)

- `Fetcher`:
  - Artisi: daha hafif.
  - Eksisi: fetcher extra bagimliliklari gerekebilir.
  - Durum: opsiyonel capability.

- `DynamicFetcher`:
  - Artisi: JS agir sayfalarda daha yuksek parse sansi.
  - Eksisi: browser otomasyonu ve maliyet.
  - Durum: bu milestone'da aktif kullanilmiyor.

- `StealthyFetcher`:
  - Artisi: korumali sayfalarda teknik olarak daha agresif deneme.
  - Eksisi: guvenlik/politika riski.
  - Durum: bu milestone'da aktif kullanilmiyor.

## Guvenli kullanim sekli

- Sadece exact watchlist URL.
- Sadece public, erisilebilir sayfalar.
- robots/policy preflight zorunlu.
- Saved HTML fixture parse modu desteklenir.
- Observation kayitlari varsayilan internal-only.

## Sonuc

Scrapling, parser katmaninda faydali bir gelistirme araci olarak uygundur. Network/fetch katmaninda ise sadece SAFE_FETCH politikasiyla, bypass tekniklerine girmeden kullanilmalidir.

