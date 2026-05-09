# DEVELOPMENT_WORKFLOW.md — Geliştirme İş Akışı

## Hızlı Başlangıç

```powershell
# Projeyi klonla
git clone https://github.com/chaglaruk/BasketScoutDataService
cd BasketScoutDataService

# Tek komutla başlat
.\scripts\dev.ps1
```

`.\scripts\dev.ps1` otomatik olarak:
1. `.venv` sanal ortamını oluşturur (Python 3.11+)
2. `requirements.txt` bağımlılıklarını yükler
3. `.env` dosyasını oluşturur (`.env.example`'dan)
4. SQLite veritabanını başlatır
5. Demo veriyi ekler
6. FastAPI sunucusunu `http://127.0.0.1:8787` adresinde başlatır

---

## Kullanılabilir Scriptler

| Script | Açıklama |
|---|---|
| `.\scripts\dev.ps1` | Geliştirme sunucusunu başlatır |
| `.\scripts\test.ps1` | pytest çalıştırır |
| `.\scripts\lint.ps1` | ruff lint çalıştırır |
| `.\scripts\smoke.ps1` | Canlı endpoint smoke testi |
| `.\scripts\doctor.ps1` | Ortam sağlık kontrolü |
| `.\scripts\run.ps1` | Sadece sunucuyu başlatır |

---

## VS Code ile Geliştirme

Projeyi VS Code'da açmak için:

```powershell
code C:\Users\Caglar\Desktop\BasketScoutDataService
```

Önerilen eklentiler:
- Python (Microsoft)
- Ruff (Astral Software)
- REST Client (Huachao Mao)

`.vscode/tasks.json` (isteğe bağlı, eklenebilir):
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Dev Server",
      "type": "shell",
      "command": ".\\scripts\\dev.ps1",
      "group": "build"
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": ".\\scripts\\test.ps1",
      "group": "test"
    }
  ]
}
```

---

## Ortam Değişkenleri

`.env.example` dosyasını `.env` olarak kopyalayın ve düzenleyin:

```powershell
Copy-Item .env.example .env
```

**Önemli:** `.env` dosyasını asla git'e eklemeyin.

---

## Yeni Provider Ekleme

1. `app/providers/` altında yeni dosya oluşturun.
2. `BaseProvider` ABC'yi uygulayın.
3. `ProviderRegistry._build()` içine ekleyin.
4. `tests/` altına test yazın.
5. `PROVIDER_STATUS.md` dosyasını güncelleyin.

---

## Commit ve Push

```powershell
git add .
git commit -m "feat: yeni özellik açıklaması"
git push origin main
```

Her milestone sonrası push yapın.

---

## Bağımlılık Güncelleme

```powershell
.venv\Scripts\pip.exe install --upgrade -r requirements.txt
```

---

## Veritabanı Sıfırlama

```powershell
Remove-Item data\basketscout.db -ErrorAction SilentlyContinue
.\scripts\dev.ps1
```
