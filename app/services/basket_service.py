"""BasketService - sepet karsilastirma servisi."""

from __future__ import annotations

import logging
from collections import defaultdict

from app.domain.basket_optimizer import compare_basket
from app.domain.models import BasketCompareRequest, BasketCompareResponse, PriceItem
from app.services.cache_policy import determine_data_mode
from app.services.price_service import PriceService

logger = logging.getLogger(__name__)


class BasketService:
    def __init__(self) -> None:
        self._price_service = PriceService()

    def compare(self, request: BasketCompareRequest) -> BasketCompareResponse:
        """Sepet karsilastirmasi yapar."""
        product_names = [item.name for item in request.items]

        price_result = self._price_service.get_latest(product_names, postcode=request.postcode)
        raw_prices = price_result.items

        by_retailer: dict[str, list[PriceItem]] = defaultdict(list)
        for item in raw_prices:
            by_retailer[item.retailer_slug].append(item)

        warnings: list[str] = []
        if price_result.any_stale:
            warnings.append(
                "Bazi fiyat verileri guncel degil (TTL asildi). Dogruluk azalabilir."
            )
        if price_result.why_mock_used:
            warnings.append(price_result.why_mock_used)
        if any(item.source == "Observed web price" for item in raw_prices):
            warnings.append("Observed from public web page. Price may change.")

        response = compare_basket(
            request=request,
            price_data=dict(by_retailer),
            data_mode=determine_data_mode(raw_prices),
            warnings=warnings,
        )
        _apply_metadata(response, raw_prices, price_result.why_mock_used)
        return response


def _apply_metadata(
    response: BasketCompareResponse,
    raw_prices: list[PriceItem],
    why_mock_used: str | None,
) -> None:
    source_counts: dict[str, int] = {}
    for item in raw_prices:
        if item.source:
            source_counts[item.source] = source_counts.get(item.source, 0) + 1

    response.metadata.line_source_summary = source_counts
    response.metadata.provider_used = _provider_used_label(source_counts)
    response.metadata.why_mock_used = why_mock_used
    response.metadata.last_checked_at = max(
        (item.last_checked_at for item in raw_prices),
        default=None,
    )
    response.metadata.freshness = "stale" if any(item.is_stale for item in raw_prices) else "fresh"
    response.metadata.confidence = _confidence_label(raw_prices)


def _provider_used_label(source_counts: dict[str, int]) -> str | None:
    if not source_counts:
        return None
    if len(source_counts) == 1:
        return next(iter(source_counts))
    return "mixed"


def _confidence_label(items: list[PriceItem]) -> str | None:
    if not items:
        return None
    minimum = min(item.confidence for item in items)
    if minimum >= 0.9:
        return "high"
    if minimum >= 0.6:
        return "medium"
    return "low"
