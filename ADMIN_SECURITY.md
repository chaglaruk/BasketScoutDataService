# ADMIN_SECURITY.md — Yönetici Paneli Güvenliği

BasketScoutDataService, manuel fiyat içe aktarma ve veri yenileme gibi kritik işlemler için yönetici endpoint'leri sunar. Bu endpoint'lerin güvenliği için şu yöntemler kullanılabilir:

## 1. Token Tabanlı Güvenlik (Önerilen)

`.env` dosyasında `ADMIN_TOKEN` değişkenini tanımlayarak endpoint'leri korumaya alabilirsiniz.

**Yapılandırma (.env):**
```bash
ADMIN_TOKEN=senin_guclu_token_degerin
```

Bu durumda, `/admin/*` endpoint'lerine yapılan tüm isteklere `X-Admin-Token` başlığı (header) eklenmelidir.

**Örnek İstek (curl):**
```bash
curl -X GET http://127.0.0.1:8787/admin/manual-prices \
     -H "X-Admin-Token: senin_guclu_token_degerin"
```

Eğer token yanlışsa veya eksikse `401 Unauthorized` hatası döndürülür.

## 2. Yerel / Geliştirme Modu

Eğer `ADMIN_TOKEN` ayarlanmamışsa, admin endpoint'leri herhangi bir doğrulama gerektirmeden çalışır. Bu mod sadece yerel testler ve geliştirme aşaması için uygundur. Üretim (production) ortamında kesinlikle bir token ayarlanmalıdır.

## 3. Erişim Kısıtlamaları

Admin endpoint'leri varsayılan olarak `/admin` prefix'i altındadır. Eğer backend servisinizi internete açıyorsanız, bir reverse proxy (Nginx, Caddy vb.) kullanarak sadece belirli IP adreslerinden gelen `/admin` isteklerine izin vermeniz önerilir.
