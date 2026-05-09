# PRODUCT_SPEC.md — Ürün Spesifikasyonu

## Vizyon

BasketScoutDataService, İngiltere'deki tüketicilere en ucuz bakkal sepeti
tercihini bulmalarında yardımcı olan BasketScout Android uygulamasının
backend veri altyapısıdır.

## Temel Gereksinimler

### Fonksiyonel

- Bakkal ürünlerini isim ve alias ile ara
- Birden fazla perakendecinin güncel fiyatlarını getir
- Verilen sepeti perakendeciler arasında karşılaştır
- En ucuz ve kapsamayı karşılayan mağazayı öner
- Sadakat fiyatı ve kendi marka seçeneklerini destekle
- Veri tazeliği ve güven skorunu raporla

### Veri Gereksinimleri

- Kaynak: İngilizce satılan bakkal ürünleri
- Kapsamı: İngiltere perakendecileri (Tesco, Asda, Sainsbury's, Morrisons, Waitrose, Co-op, Aldi, Lidl)
- Para birimi: GBP
- Tazelik: Fiyat TTL 6 saat, stok TTL 1 saat

### Güvenilirlik

- Provider hataları izole — bir provider diğerlerini çökertmemeli
- Canlı veri yoksa cache kullan
- Cache yoksa mock kullan
- Her yanıtta veri modu belirt: mock | live | cache | mixed

## Dışlananlar (Bu Repoda Yok)

- Android uygulaması kodu
- Kullanıcı hesap yönetimi
- Ödeme işleme
- Ürün görselleri (ileride eklenebilir)

## Başarı Kriterleri

- Sepet karşılaştırma yanıt süresi < 2 saniye (mock modda)
- Tüm testler CI'da geçiyor
- Mock provider her zaman çalışıyor
- Tek komutla yerel geliştirme başlatılabiliyor
