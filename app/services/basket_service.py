"""BasketService — sepet karşılaştırma servisi."""

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
        """Sepet karşılaştırması yapar."""
        product_names = [item.name for item in request.items]

        raw_prices, any_stale = self._price_service.get_latest(
            product_names, postcode=request.postcode
        )

        # Perakendeciye göre grupla
        by_retailer: dict[str, list[PriceItem]] = defaultdict(list)
        for p in raw_prices:
            by_retailer[p.retailer_slug].append(p)

        warnings: list[str] = []
        if any_stale:
            warnings.append(
                "Bazı fiyat verileri güncel değil (TTL aşıldı). Doğruluk azalmış olabilir."
            )

        data_mode = determine_data_mode(raw_prices)

        return compare_basket(
            request=request,
            price_data=dict(by_retailer),
            data_mode=data_mode,
            warnings=warnings,
        )
