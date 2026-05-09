"""ManualImportService — manuel fiyat verilerini yönetir."""
from __future__ import annotations

import csv
import logging
from pathlib import Path

from app.domain.models import ManualImportSummary, ManualPriceImportItem
from app.domain.normalization import normalize_name

logger = logging.getLogger(__name__)


class ManualImportService:
    def __init__(self, csv_path: Path = Path("data/manual_import/sample_prices.csv")) -> None:
        self._csv_path = csv_path

    def get_all(self) -> list[ManualPriceImportItem]:
        """Tüm manuel fiyatları döndürür."""
        if not self._csv_path.exists():
            return []

        items = []
        with open(self._csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    items.append(
                        ManualPriceImportItem(
                            retailer=row.get("retailer", ""),
                            retailer_slug=row.get("retailer_slug"),
                            product_name=row.get("product_name", ""),
                            alias=row.get("alias"),
                            category=row.get("category"),
                            price=float(row.get("price", 0)),
                            loyalty_price=float(row["loyalty_price"]) if row.get("loyalty_price") else None,
                            available=row.get("available", "").lower() in ("true", "yes", "1"),
                            postcode=row.get("postcode"),
                            source_url=row.get("source_url"),
                        )
                    )
                except (ValueError, TypeError):
                    continue
        return items

    def import_items(self, items: list[ManualPriceImportItem]) -> ManualImportSummary:
        """Yeni öğeleri içe aktarır ve CSV'yi günceller."""
        imported = 0
        skipped = 0
        errors = []

        # Mevcut verileri yükle
        existing_items = self.get_all()
        # Anahtar: (retailer_slug, product_name)
        data_map = {
            (i.retailer_slug or normalize_name(i.retailer), i.product_name): i
            for i in existing_items
        }

        for item in items:
            if not item.retailer or not item.product_name:
                skipped += 1
                errors.append(f"Eksik veri: {item.product_name or 'Bilinmeyen ürün'}")
                continue

            slug = item.retailer_slug or normalize_name(item.retailer)
            key = (slug, item.product_name)
            data_map[key] = item
            imported += 1

        # CSV'ye yaz
        self._save_to_csv(list(data_map.values()))

        return ManualImportSummary(
            rows_imported=imported,
            rows_skipped=skipped,
            validation_errors=errors,
        )

    def get_template_csv(self) -> str:
        """CSV şablonu döndürür."""
        headers = [
            "retailer", "retailer_slug", "product_name", "alias", "category",
            "price", "loyalty_price", "available", "postcode", "source_url", "last_checked_at"
        ]
        return ",".join(headers) + "\n"

    def _save_to_csv(self, items: list[ManualPriceImportItem]) -> None:
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "retailer", "retailer_slug", "product_name", "alias", "category",
            "price", "loyalty_price", "available", "postcode", "source_url", "last_checked_at"
        ]
        with open(self._csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for item in items:
                writer.writerow({
                    "retailer": item.retailer,
                    "retailer_slug": item.retailer_slug or normalize_name(item.retailer),
                    "product_name": item.product_name,
                    "alias": item.alias,
                    "category": item.category,
                    "price": item.price,
                    "loyalty_price": item.loyalty_price,
                    "available": "true" if item.available else "false",
                    "postcode": item.postcode,
                    "source_url": item.source_url,
                    "last_checked_at": item.last_checked_at.isoformat() if item.last_checked_at else "",
                })
