"""availability_service paketi — stok durumu servisi."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem
from app.services.provider_registry import get_registry

logger = logging.getLogger(__name__)


class AvailabilityService:
    def get_availability(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        """Ürün stok durumunu döndürür (fiyat snapshot'ından alınır)."""
        registry = get_registry()
        return registry.get_prices(product_names, postcode=postcode)
