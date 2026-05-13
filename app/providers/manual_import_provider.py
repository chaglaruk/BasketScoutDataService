"""ManualImportProvider — CSV dosyasından fiyat verisi okur."""
from __future__ import annotations

import csv
import logging
from datetime import UTC
from pathlib import Path

from app.core.time import utcnow
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.domain.normalization import normalize_name
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

_DEFAULT_CSV_PATH = Path("data/manual_import/sample_prices.csv")
_RETAILER_DISPLAY_NAMES = {
    "tesco": "Tesco",
    "asda": "Asda",
    "sainsburys": "Sainsbury's",
    "aldi": "Aldi",
    "lidl": "Lidl",
    "morrisons": "Morrisons",
    "waitrose": "Waitrose",
    "coop": "Co-op",
    "iceland": "Iceland",
    "ocado": "Ocado",
    "mands": "M&S Food",
    "farmfoods": "Farmfoods",
}


class ManualImportProvider(BaseProvider):
    """
    CSV dosyasından fiyat verisi yükleyen provider.

    Beklenen sütunlar:
    retailer, retailer_slug, product_name, alias, category, price,
    loyalty_price, available, postcode, source_url, last_checked_at

    Tüm sütunlar opsiyoneldir. Minimum: retailer + product_name + price
    """

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_path = csv_path or _DEFAULT_CSV_PATH
        self._data: list[dict] = []
        self._loaded = False
        self._load_error: str | None = None

    @property
    def name(self) -> str:
        return "manual_import"

    @property
    def type(self) -> str:
        return "manual"

    @property
    def limitations(self) -> list[str]:
        return [
            "Veri kaynağı CSV dosyasıdır — gerçek zamanlı değil.",
            f"CSV yolu: {self._csv_path}",
            "Verinin doğruluğu ve güncelliği dosyayı güncelleyen kişiye bağlıdır.",
        ]

    def reload(self) -> None:
        """Verileri yeniden yükler."""
        self._loaded = False
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._csv_path.exists():
            self._load_error = f"CSV dosyası bulunamadı: {self._csv_path}"
            logger.warning(self._load_error)
            return
        try:
            with open(self._csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self._data = list(reader)
            logger.info(f"ManualImport: {len(self._data)} satır yüklendi — {self._csv_path}")
        except Exception as exc:
            self._load_error = f"CSV okuma hatası: {exc}"
            logger.error(self._load_error)

    def status(self) -> ProviderStatusItem:
        self._ensure_loaded()
        if self._load_error:
            st = "limited"
            msg = self._load_error
        else:
            st = "ok"
            msg = f"{len(self._data)} fiyat kaydı yüklendi."
        return ProviderStatusItem(
            name=self.name,
            status=st,
            type=self.type,
            last_run_at=utcnow(),
            message=msg,
            limitations=self.limitations,
            supports_live_prices=False,
            supports_stock=False,
            confidence_score=0.7,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        self._ensure_loaded()
        nq = normalize_name(query)
        seen: dict[str, ProductSummary] = {}
        for row in self._data:
            pname = row.get("product_name", "")
            if not pname:
                continue
            nn = normalize_name(pname)
            alias = normalize_name(row.get("alias", ""))
            if (nq in nn or nn in nq or (alias and (nq in alias or alias in nq))) and nn not in seen:
                    seen[nn] = ProductSummary(
                        id=hash(nn) % 999999,
                        canonical_name=pname,
                        category=row.get("category"),
                        aliases=[row.get("alias", "")] if row.get("alias") else [],
                        source=self.name,
                        confidence=0.7,
                    )
        return list(seen.values())

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        self._ensure_loaded()
        results: list[PriceItem] = []
        now = utcnow()

        for name in product_names:
            nq = normalize_name(name)
            for row in self._data:
                pname = row.get("product_name", "")
                if not pname:
                    continue
                alias = normalize_name(row.get("alias", ""))
                normalized_product = normalize_name(pname)
                if (
                    nq not in normalized_product
                    and normalized_product not in nq
                    and not (alias and (nq in alias or alias in nq))
                ):
                    continue
                # Posta kodu filtresi (opsiyonel)
                if postcode and row.get("postcode") and not row["postcode"].upper().startswith(postcode.upper()[:3]):
                        continue
                try:
                    price = float(row.get("price", 0))
                except (ValueError, TypeError):
                    continue
                loyalty = None
                if row.get("loyalty_price"):
                    import contextlib
                    with contextlib.suppress(ValueError, TypeError):
                        loyalty = float(row["loyalty_price"])
                available_raw = row.get("available", "").lower()
                available = None
                if available_raw in ("true", "yes", "1"):
                    available = True
                elif available_raw in ("false", "no", "0"):
                    available = False

                from datetime import datetime
                try:
                    lc = datetime.fromisoformat(row["last_checked_at"]) if row.get("last_checked_at") else now
                    if lc.tzinfo is None:
                        lc = lc.replace(tzinfo=UTC)
                except (ValueError, TypeError):
                    lc = now

                results.append(
                    PriceItem(
                        retailer=_retailer_name(row),
                        retailer_slug=_retailer_slug(row),
                        product=pname,
                        price=price,
                        currency="GBP",
                        loyalty_price=loyalty,
                        available=available,
                        source=self.name,
                        source_url=row.get("source_url"),
                        last_checked_at=lc,
                        confidence=0.7,
                        is_stale=False,
                    )
                )
        return results


def _retailer_slug(row: dict) -> str:
    slug = (row.get("retailer_slug") or "").strip()
    if slug:
        return slug
    return normalize_name((row.get("retailer") or "unknown").strip())


def _retailer_name(row: dict) -> str:
    name = (row.get("retailer") or "").strip()
    if name:
        return name
    slug = _retailer_slug(row)
    return _RETAILER_DISPLAY_NAMES.get(slug, slug.replace("_", " ").title() or "Unknown")
