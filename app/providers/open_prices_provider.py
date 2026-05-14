"""OpenPricesProvider - open/crowdsourced historical price data."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.time import utcnow
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://prices.openfoodfacts.org/api/v1"
_OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
_USER_AGENT = "BasketScoutDataService/0.1.0 (contact: local-development)"


class OpenPricesProvider(BaseProvider):
    """Open Prices crowdsourced prices.

    This is real open/crowdsourced data when available, but it is not a
    retailer-operated live feed and it does not provide stock availability.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=_BASE_URL,
            timeout=10.0,
            headers={"User-Agent": _USER_AGENT},
        )
        self._last_failure_reason: str | None = None

    @property
    def name(self) -> str:
        return "open_prices"

    @property
    def type(self) -> str:
        return "open_data"

    @property
    def supports_live_prices(self) -> bool:
        return False

    @property
    def supports_stock(self) -> bool:
        return False

    @property
    def limitations(self) -> list[str]:
        base = [
            "Crowdsourced/open data, not an official retailer live feed.",
            "UK coverage varies by barcode, store and contributor activity.",
            "Historical prices can be old and confidence is capped at 0.6.",
            "Stock availability is not provided.",
        ]
        if self._last_failure_reason:
            base.append(f"Last fallback reason: {self._last_failure_reason}")
        return base

    def status(self) -> ProviderStatusItem:
        try:
            r = self._client.get("/prices", params={"page_size": 1}, timeout=5.0)
            if r.status_code == 200:
                st, msg = "ok", "Open Prices API is reachable; useful UK grocery matches are partial."
            else:
                st, msg = "limited", f"Open Prices HTTP {r.status_code}"
        except Exception as exc:
            st, msg = "limited", f"Open Prices connection error: {exc}"
        return ProviderStatusItem(
            name=self.name,
            status=st,
            type=self.type,
            last_run_at=utcnow(),
            message=msg,
            limitations=self.limitations,
            supports_live_prices=self.supports_live_prices,
            supports_stock=self.supports_stock,
            confidence_score=0.6,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        # Product metadata comes from OpenFoodFactsProvider. OpenPrices is
        # price-first and requires barcodes, so search stays intentionally empty.
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        results: list[PriceItem] = []
        for name in product_names:
            try:
                barcodes = self._candidate_barcodes(name)
                if not barcodes:
                    self._last_failure_reason = f"No OpenFoodFacts barcode candidate for '{name}'."
                    continue
                price = self._first_gbp_price(barcodes)
                if price is None:
                    self._last_failure_reason = f"No GBP OpenPrices row for '{name}' candidates."
                    continue
                results.append(self._price_item(name, price))
            except Exception as exc:
                self._last_failure_reason = f"OpenPrices error for '{name}': {exc}"
                logger.warning(self._last_failure_reason)
        return results

    def _candidate_barcodes(self, name: str) -> list[str]:
        response = httpx.get(
            _OFF_SEARCH_URL,
            params={
                "search_terms": name,
                "search_simple": 1,
                "json": 1,
                "page_size": 5,
                "countries_tags_en": "United Kingdom",
                "fields": "code,product_name,product_name_en,countries_tags",
            },
            timeout=5.0,
            headers={"User-Agent": _USER_AGENT},
        )
        if response.status_code != 200:
            return []
        products = response.json().get("products", [])
        barcodes: list[str] = []
        for product in products:
            code = str(product.get("code") or product.get("_id") or "").strip()
            if code and code not in barcodes:
                barcodes.append(code)
        return barcodes

    def _first_gbp_price(self, barcodes: list[str]) -> dict[str, Any] | None:
        for barcode in barcodes:
            response = self._client.get(
                "/prices",
                params={
                    "product_code": barcode,
                    "currency": "GBP",
                    "page_size": 5,
                    "order_by": "-date",
                },
                timeout=5.0,
            )
            if response.status_code != 200:
                continue
            for item in response.json().get("items", []):
                currency = str(item.get("currency") or "").upper()
                if currency and currency != "GBP":
                    continue
                try:
                    price_value = float(item.get("price", 0.0))
                except (TypeError, ValueError):
                    continue
                if price_value <= 0:
                    continue
                item["product_code"] = barcode
                item["price"] = price_value
                item["currency"] = currency or "GBP"
                return item
        return None

    def _price_item(self, requested_name: str, raw: dict[str, Any]) -> PriceItem:
        checked_at = _parse_open_prices_date(raw) or utcnow()
        shop_name = _shop_name(raw)
        barcode = raw.get("product_code") or raw.get("code") or "unknown"
        return PriceItem(
            retailer=shop_name,
            retailer_slug="open_prices",
            product=f"{requested_name} ({barcode})",
            price=float(raw["price"]),
            currency=str(raw.get("currency") or "GBP"),
            loyalty_price=None,
            own_brand=False,
            available=None,
            source=self.name,
            source_url=f"https://prices.openfoodfacts.org/product/{barcode}",
            last_checked_at=checked_at,
            confidence=0.55,
            is_stale=False,
        )


def _parse_open_prices_date(raw: dict[str, Any]) -> datetime | None:
    for key in ("date", "created", "created_at", "updated_at"):
        value = raw.get(key)
        if not value:
            continue
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    return None


def _shop_name(raw: dict[str, Any]) -> str:
    for key in ("location_osm_name", "shop_name", "location", "proof_location"):
        value = raw.get(key)
        if isinstance(value, dict):
            value = value.get("name") or value.get("display_name")
        if value:
            return str(value)
    return "OpenPrices (crowdsourced)"
