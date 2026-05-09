"""PriceService — fiyat sorgulama servisi."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem
from app.services.cache_policy import annotate_staleness
from app.services.provider_registry import get_registry

logger = logging.getLogger(__name__)


class PriceService:
    def get_latest(
        self,
        product_names: list[str],
        postcode: str | None = None,
        provider_names: list[str] | None = None,
    ) -> tuple[list[PriceItem], bool]:
        """
        Verilen ürünler için en güncel fiyatları döndürür.

        Dönüş: (items, any_stale)
        """
        registry = get_registry()
        raw = registry.get_prices(product_names, postcode=postcode, provider_names=provider_names)
        return annotate_staleness(raw)
