"""ProductService — ürün arama ve yönetim servisi."""

from __future__ import annotations

import logging

from app.domain.models import ProductSummary
from app.services.provider_registry import get_registry

logger = logging.getLogger(__name__)


class ProductService:
    def search(
        self,
        query: str,
        provider_names: list[str] | None = None,
    ) -> list[ProductSummary]:
        """Ürün arar, provider'lardan sonuçları toplar."""
        if not query or not query.strip():
            return []
        registry = get_registry()
        results = registry.search_products(query.strip(), provider_names=provider_names)
        # Tekrarları kaldır (aynı canonical isim)
        seen: set[str] = set()
        unique: list[ProductSummary] = []
        for r in results:
            key = r.canonical_name.lower()
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
