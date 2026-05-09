"""import_csv.py — ManualImportProvider için CSV doğrulama ve içe aktarma betiği."""

import csv
import sys
from pathlib import Path
from typing import TextIO

REQUIRED_COLUMNS = {"retailer", "retailer_slug", "product_name", "category", "price"}

def import_csv(file_stream: TextIO, target_path: Path) -> dict:
    reader = csv.DictReader(file_stream)

    if not reader.fieldnames:
        raise ValueError("CSV dosyası boş veya başlık satırı yok.")

    headers = set(reader.fieldnames)
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"Eksik zorunlu sütunlar: {', '.join(missing)}")

    valid_rows = []
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            # Temel doğrulama
            if not row["retailer"].strip():
                raise ValueError("retailer boş olamaz")
            if not row["retailer_slug"].strip():
                raise ValueError("retailer_slug boş olamaz")
            if not row["product_name"].strip():
                raise ValueError("product_name boş olamaz")

            # Fiyat doğrulama
            price_str = row["price"].strip()
            if not price_str:
                raise ValueError("price boş olamaz")
            try:
                price = float(price_str)
                if price <= 0:
                    raise ValueError("price 0'dan büyük olmalıdır")
            except ValueError as err:
                raise ValueError(f"Geçersiz fiyat formatı: {price_str}") from err

            valid_rows.append(row)

        except ValueError as e:
            errors.append(f"Satır {i}: {e}")

    if errors:
        return {"success": False, "errors": errors, "imported": 0}

    # Yazma işlemi (varsayılan CSV'yi günceller)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(valid_rows)

    return {"success": True, "errors": [], "imported": len(valid_rows)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python -m app.scripts.import_csv <csv_dosya_yolu>")
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Hata: Dosya bulunamadı: {source_file}")
        sys.exit(1)

    target = Path("data/manual_import/sample_prices.csv")

    with open(source_file, encoding="utf-8") as f:
        try:
            result = import_csv(f, target)
            if result["success"]:
                print(f"Başarılı! {result['imported']} satır içe aktarıldı.")
                print(f"Hedef: {target.absolute()}")
            else:
                print("Hata: CSV doğrulama başarısız oldu.")
                for err in result["errors"]:
                    print(f" - {err}")
                sys.exit(1)
        except Exception as e:
            print(f"Beklenmeyen hata: {e}")
            sys.exit(1)
