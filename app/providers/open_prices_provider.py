"""OpenPricesProvider — açık/kitlesel kaynaklı fiyat verileri."""

from __future__ import annotations

import logging

import httpx

from app.core.time import utcnow
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Open Prices API — https://prices.openfoodfacts.org
_BASE_URL = "https://prices.openfoodfacts.org/api/v1"


class OpenPricesProvider(BaseProvider):
    """
    Open Prices (prices.openfoodfacts.org) — kitlesel kaynaklı fiyat verileri.

    SINIRLILIKLAR:
    - Resmi süpermarket fiyatı DEĞİLDİR.
    - Kullanıcı tarafından girilen veriler — yanlış veya eski olabilir.
    - Güven skoru 0.6 tavanla sınırlandırılmıştır.
    - İngiltere kapsamı sınırlıdır.
    - Stok bilgisi sunmaz.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=_BASE_URL,
            timeout=10.0,
            headers={"User-Agent": "BasketScoutDataService/0.1.0"},
        )

    @property
    def name(self) -> str:
        return "open_prices"

    @property
    def type(self) -> str:
        return "open_data"

    @property
    def supports_live_prices(self) -> bool:
        return True

    @property
    def limitations(self) -> list[str]:
        return [
            "Kitlesel kaynaklı veri — resmi fiyat garantisi yok.",
            "Güven skoru maksimum 0.6 ile sınırlıdır.",
            "İngiltere kapsamı sınırlıdır.",
            "Stok bilgisi sunmaz.",
            "İnternet bağlantısı gerektirir.",
        ]

    def status(self) -> ProviderStatusItem:
        try:
            r = self._client.get("/prices", params={"page_size": 1}, timeout=5.0)
            if r.status_code == 200:
                st, msg = "ok", "Open Prices API erişilebilir."
            else:
                st, msg = "limited", f"HTTP {r.status_code}"
        except Exception as exc:
            st, msg = "limited", f"Bağlantı hatası: {exc}"
        return ProviderStatusItem(
            name=self.name,
            status=st,
            type=self.type,
            last_run_at=utcnow(),
            message=msg,
            limitations=self.limitations,
            supports_live_prices=self.supports_live_prices,
            supports_stock=self.supports_stock,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        results = []
        for name in product_names:
            try:
                # 1. Open Food Facts'ten barkod al (İngiltere odaklı)
                off_r = httpx.get(
                    "https://world.openfoodfacts.org/cgi/search.pl",
                    params={"search_terms": name, "search_simple": 1, "json": 1, "page_size": 1, "country": "united-kingdom"},
                    timeout=5.0,
                    headers={"User-Agent": "BasketScoutDataService/0.1.0"}
                )
                if off_r.status_code != 200:
                    continue
                off_data = off_r.json()
                products = off_data.get("products", [])
                if not products:
                    continue
                barcode = products[0].get("_id")
                if not barcode:
                    continue

                # 2. Barkod ile Open Prices'tan fiyat sorgula
                r = self._client.get("/prices", params={"product_code": barcode, "page_size": 1}, timeout=5.0)
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("items", [])
                    if items:
                        best_price = items[0]
                        price_val = float(best_price.get("price", 0.0))
                        if price_val > 0:
                            results.append(PriceItem(
                                retailer="OpenPrices (Crowdsourced)",
                                retailer_slug="open_prices",
                                product=name,
                                price=price_val,
                                currency=best_price.get("currency", "GBP"),
                                loyalty_price=None,
                                own_brand=False,
                                available=None,
                                source=self.name,
                                source_url=f"https://prices.openfoodfacts.org/api/v1/prices?product_code={barcode}",
                                last_checked_at=utcnow(),
                                confidence=0.6,
                                is_stale=False,
                            ))
            except Exception as exc:
                logger.warning(f"OpenPrices error for {name}: {exc}")
        return results
