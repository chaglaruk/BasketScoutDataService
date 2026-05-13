"""PriceService — fiyat sorgulama servisi."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.domain.models import PriceItem
from app.services.cache_policy import annotate_staleness
from app.services.provider_registry import get_registry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PriceQueryResult:
    items: list[PriceItem]
    any_stale: bool
    why_mock_used: str | None = None


class PriceService:
    def get_latest(
        self,
        product_names: list[str],
        postcode: str | None = None,
        provider_names: list[str] | None = None,
    ) -> PriceQueryResult:
        """
        Verilen ürünler için en güncel fiyatları döndürür.

        Dönüş: (items, any_stale)
        """
        registry = get_registry()
        raw = registry.get_prices_with_metadata(
            product_names,
            postcode=postcode,
            provider_names=provider_names,
        )
        items, any_stale = annotate_staleness(raw.items)
        return PriceQueryResult(
            items=items,
            any_stale=any_stale,
            why_mock_used=raw.why_mock_used,
        )
