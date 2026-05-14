# SCRAPLING_USAGE_POLICY.md

Bu belge BasketScoutDataService Scrapling kullanim modlarini ve sinirlarini tanimlar.

## MODE 1: SAFE_FETCH

Kurallar:

- Sadece enabled watchlist satiri + exact `product_url`.
- Sadece `http/https` URL.
- robots/policy preflight zorunlu.
- Login/session auth yok.
- Captcha cozumleme yok.
- Proxy rotation yok.
- Stealth bypass yok.
- Private API veya gizli endpoint yok.
- Katalog crawl/link discovery/pagination yok.
- Stock her zaman `Unknown`.

Davranis:

- Erisim blokaji algilanirsa `BLOCKED_BY_ACCESS_CONTROL` kaydedilir.
- Policy blokajinda `BLOCKED_BY_ROBOTS_OR_POLICY` kaydedilir.
- Parse basarisizsa `PARSE_FAILED`.

## MODE 2: FIXTURE_PARSE

Kurallar:

- Sadece local fixture HTML dosyalari parse edilir.
- Network cagrisi yok.
- Test ve parser gelistirme icin kullanilir.

Davranis:

- Price extraction parser testi burada kosulur.
- Blocked/no-price fixture senaryolari burada dogrulanir.

## Public Gosterim Kurali

- Varsayilan: `public_display_allowed=false`.
- Public kullanima gecis icin:
  - `public_display_allowed=true`
  - `rights_status=public_allowed`
  - confidence threshold kosulu

Bu kosullar disindaki kayitlar internal/admin amacli kalir.

