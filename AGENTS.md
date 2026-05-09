# AGENTS.md — Otonom Ajan Kuralları

Bu dosya, bu depoda çalışan tüm AI otonom ajanlar için bağlayıcı kurallar tanımlar.

## Kimlik

Proje: **BasketScoutDataService**
Dil: Python 3.11+ / FastAPI
Görev: İngiltere bakkal fiyat verisi backend'i

## Temel Kurallar

### Güvenlik

- `.env` dosyasına hiçbir zaman sır, API anahtarı veya parola ekleme.
- Yalnızca `.env.example` kullan.
- Git geçmişinde sır bırakma.

### Scraping Politikası

- Captcha bypass YASAKTIR.
- Login bypass YASAKTIR.
- Paywall bypass YASAKTIR.
- Bot koruması atlama YASAKTIR.
- Süpermarket sitelerini aşırı yükleme — rate limit uygula.
- Yalnızca herkese açık sayfalara eriş.
- robots.txt'e saygı göster.

### Veri Doğruluğu

- Mock/demo verisi ile canlı verisi açıkça ayrılmalı.
- Her fiyat yanıtı `source`, `confidence`, `last_checked_at` içermeli.
- Stale veri `is_stale: true` ile işaretlenmeli.
- Canlı stok doğruluğu konusunda yanlış iddiada bulunma.

### Provider Mimarisi

- Her provider bağımsız çalışmalı.
- Bir provider hatası diğerlerini etkilememeli.
- Canlı scraping başarısız olursa cache veya mock'a dön.
- Provider durumları açıkça raporlanmalı: ok | limited | blocked | error.

### Kod Kalitesi

- Tip işaretleri zorunlu.
- Bare `except:` yasak — en az `Exception` yakalayın.
- Küçük, odaklı fonksiyonlar.
- Spekülatif soyutlamadan kaçın.
- Yeni domain mantığı için test yaz.

## Otonom Çalışma Kuralları

- Komut çalıştırmadan önce hedef dizini incele.
- İlgisiz dosyalar varsa dur ve BLOCKED raporla.
- Her milestone'dan sonra commit ve push yap.
- GitHub auth yoksa local'de devam et, BLOCKED raporla.
- Testler geçmeden commit yapma.
- Kısa, milestone bazlı yanıtlar ver.

## Yasaklı Eylemler

- Süpermarket hesabına giriş yapma.
- Ödeme duvarı olan içeriğe erişme.
- Gizli/hesap bazlı veri scrape etme.
- Android uygulaması kodu yazma (bu repo yalnızca backend).
- Gerçekmiş gibi sahte canlı veri üretme.

## Milestone Sırası

0. Proje/repo kurulumu
1. Mock çalışan API
2. Provider mimarisi + cache
3. Açık veri provider'ları
4. Perakendeci scraping güvenli spike
5. Scheduler/refresh sistemi
6. Android entegrasyon sözleşmesi
7. Yerel geliştirme el teslimi
8. Son QA

## Belge Dili

Belgeler Türkçe yazılır. Kod tanımlayıcıları İngilizce kalır.
