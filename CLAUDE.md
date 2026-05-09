# CLAUDE.md — AI Yardımcı Talimatları

Bu dosya, Claude (ve benzer AI asistanları) için bu projede çalışırken uyulması
gereken ihtiyat, sadelik ve cerrahi değişiklik kurallarını tanımlar.

## Temel İlke

> Az değişiklik, doğru değişiklik.

Her değişiklik en küçük, en odaklı müdahale olmalı.
Spekülatif refactor, gereksiz soyutlama veya "ileride lazım olabilir" kodu yasaktır.

## Önce Anla

1. Talebi tam olarak kavra.
2. İlgili dosyaları oku.
3. Etkilenen testleri belirle.
4. Sonra yaz.

## Değişiklik Kuralları

- Yalnızca istenen şeyi değiştir.
- İstenmediği sürece komşu kodlara dokunma.
- Mevcut yorumları ve docstring'leri koru.
- Tip işaretlerini koru.
- `.env.example` güncel tut, `.env` git'e asla.

## Test Zorunluluğu

- Yeni domain mantığı → yeni test.
- Testler geçmeden commit önerme.
- Canlı supermarket sitelerine bağımlı unit test yazma.
- Mock HTTP kullan.

## Scraping İhtiyatı

- Scraping kodu önerildiğinde şunları kontrol et:
  - robots.txt'e uygun mu?
  - Login/captcha gerektiriyor mu? → Hayırsa geçme.
  - Rate limit uygulanıyor mu?
  - Sonuç cache'e yazılıyor mu?
- Şüphe varsa LIMITED/BLOCKED olarak işaretle ve belgele.

## Yanıt Stili

- Kısa ve odaklı yanıtlar.
- Milestone bazlı ilerleme.
- Her commit'te ne değiştiğini açıkla.
- Belirsiz gereksinimlerde sor, varsayım yapma.

## Bu Repoda Ne Yapılmaz

- Android uygulaması kodu yazılmaz.
- Ücretli API entegrasyonu eklenmez (ücretsiz açık veri hariç).
- Sahte canlı fiyat verisi üretilmez.
- Gizli veriler git'e eklenmez.
