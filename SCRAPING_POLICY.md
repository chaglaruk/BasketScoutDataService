# SCRAPING_POLICY.md — Scraping Politikası

Bu belge, BasketScoutDataService'in web scraping davranışına ilişkin
bağlayıcı kuralları tanımlar.

## Kesinlikle Yasak Eylemler

Aşağıdaki eylemler bu projede **asla** gerçekleştirilmez:

1. **Captcha bypass** — CAPTCHA çözme servisleri veya manuel bypass kullanılmaz.
2. **Login bypass** — Giriş gerektiren sayfalar ziyaret edilmez.
3. **Paywall bypass** — Ücretli içeriğe erişilmez.
4. **Bot koruması atlama** — Cloudflare, Akamai veya benzeri sistemler atlatılmaz.
5. **Özel/hesap verisi** — Kullanıcı hesabı gerektiren veriler scrape edilmez.
6. **Aşırı yükleme** — Süpermarket sitelerine yüksek frekanslı istek atılmaz.

## İzin Verilen Eylemler

- Herkese açık sayfalara saygılı HTTP GET istekleri.
- Minimum 2 saniye istek aralığı (yapılandırılabilir).
- robots.txt'e uyum.
- Şeffaf User-Agent tanımlaması:
  `BasketScoutBot/0.1 (+https://github.com/chaglaruk/BasketScoutDataService)`
- Yanıt cache'leme (TTL'ye uygun).

## Engel Durumunda Davranış

Bir perakendeci:
- CAPTCHA gösterirse → **BLOCKED** olarak işaretle, dur, belgele.
- Login gerektirirse → **BLOCKED** olarak işaretle, dur, belgele.
- 403/429 dönerse → **LIMITED** olarak işaretle, cache'e dön.
- robots.txt yasaklarsa → **BLOCKED** olarak işaretle.

Provider hatası diğer provider'ları etkilemez.
Sistem her zaman mock veya cache'e düşebilir.

## Sorumluluk Reddi

Bu servis, süpermarket web sitelerinin kullanım koşullarına uymaya çalışır.
Scraping yoluyla elde edilen veriler:
- Yalnızca herkese açık kaynaklardan alınır.
- Ticari amaçla yeniden satılmaz.
- Kullanıcıya doğruluk garantisi verilmez.

Herhangi bir perakendeci bu servisin sitelerine erişimini engellemek isterse,
`PROVIDER_STATUS.md` güncellenerek o provider BLOCKED olarak işaretlenir.
