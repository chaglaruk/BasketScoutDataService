"""OpenFoodFactsProvider — ürün meta verisi (barkod, kategori, marka)."""

from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.core.time import utcnow
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://world.openfoodfacts.org"


class OpenFoodFactsProvider(BaseProvider):
    """
    Open Food Facts API'si aracılığıyla ürün meta verisi (barkod, kategori,
    marka, besin değerleri) sağlar.

    SINIRLILIKLAR:
    - Canlı fiyat bilgisi sunmaz.
    - Stok bilgisi sunmaz.
    - Kitlesel kaynaklı veri — doğruluk %100 garantili değil.
    - İngiltere'ye özgü ürünler için 'country_tags=en:united-kingdom' filtresi kullanılır.
    - Rate limit: lütfen API'yi aşırı yüklemeyin.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = httpx.Client(
            base_url=_BASE_URL,
            headers={"User-Agent": self._settings.off_user_agent},
            timeout=10.0,
        )

    @property
    def name(self) -> str:
        return "open_food_facts"

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
        return [
            "Fiyat verisi yoktur — yalnızca ürün meta verisi.",
            "Stok bilgisi yoktur.",
            "Kitlesel kaynaklı veri — doğruluk garantisi yok.",
            "İnternet bağlantısı gerektirir.",
            "Rate limiting uygulanır — aşırı sorgu yapmayın.",
        ]

    def status(self) -> ProviderStatusItem:
        # Durum kontrolü için canlı HTTP probe yapmıyoruz — her çağrıda gecikme yaratır.
        # Canlı erişim sadece search_products/get_latest_prices sırasında test edilir.
        return ProviderStatusItem(
            name=self.name,
            status="ok",
            type=self.type,
            last_run_at=utcnow(),
            message="Open Food Facts hazir. Urun meta verisi saglar (fiyat yok).",
            limitations=self.limitations,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        try:
            r = self._client.get(
                "/cgi/search.pl",
                params={
                    "search_terms": query,
                    "search_simple": 1,
                    "json": 1,
                    "page_size": 10,
                    "country": "united-kingdom",
                },
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            logger.warning(f"OpenFoodFacts search_products hatası: {exc}")
            return []

        results: list[ProductSummary] = []
        for p in data.get("products", []):
            pname = p.get("product_name_en") or p.get("product_name") or ""
            if not pname:
                continue
            results.append(
                ProductSummary(
                    id=abs(hash(p.get("_id", pname))) % 999999,
                    canonical_name=pname,
                    category=p.get("categories", "").split(",")[0].strip() or None,
                    brand=p.get("brands", "").split(",")[0].strip() or None,
                    aliases=[p.get("_id", "")],
                    source=self.name,
                    confidence=0.7,
                )
            )
        return results

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        """Open Food Facts fiyat verisi sunmaz."""
        logger.debug("OpenFoodFacts: fiyat verisi sunmuyor.")
        return []
