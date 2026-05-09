"""TescoProvider — Tesco scraping provider (güvenli statik HTTP denemesi)."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.tesco.com/groceries/en-GB/search?query={query}&count=10"


class TescoProvider(ScrapingBaseProvider):
    """
    Tesco scraping provider.

    DURUM: LIMITED
    Tesco arama sonuçları JavaScript ile render edilir; statik HTTP yeterli değil.
    Playwright entegrasyonu gerektirir ve bot koruma sistemi aktiftir.
    Captcha veya login bypass yapılmayacaktır.

    Gelecek geliştirme:
    - Tesco resmi bir API yayınlarsa buraya eklenecek.
    - Playwright + stealth modu araştırılabilir (bot korumaya saygı göstererek).
    """

    @property
    def name(self) -> str:
        return "tesco"

    @property
    def limitations(self) -> list[str]:
        return [
            "Tesco arama JavaScript ile render edilir — statik HTTP yeterli değil.",
            "Bot koruma sistemi aktif — bypass yapılmayacak.",
            "Playwright entegrasyonu henüz eklenmedi.",
            "Giriş veya captcha gerektiren sayfalara erişilmeyecek.",
        ]

    def status(self) -> ProviderStatusItem:
        return self._limited_status(
            "Tesco statik HTTP ile erişilemiyor. Playwright gerekli. "
            "Bot korumaya saygı gösteriliyor."
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        logger.info(f"[tesco] Arama atlandı — provider LIMITED: {query}")
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        logger.info("[tesco] Fiyat alımı atlandı — provider LIMITED")
        return []
