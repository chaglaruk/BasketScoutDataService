"""MorrisonsProvider â€” Morrisons scraping provider."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)


class MorrisonsProvider(ScrapingBaseProvider):
    """
    Morrisons scraping provider.

    DURUM: LIMITED
    Morrisons arama sayfasÄ± JavaScript render ve bot koruma gerektirir.
    Captcha veya login bypass yapÄ±lmayacaktÄ±r.

    Gelecek geliÅŸtirme:
    - Resmi API yayÄ±nlanÄ±rsa eklenecek.
    - EriÅŸim politikasÄ± deÄŸiÅŸtirirse yeniden deÄŸerlendirilecek.
    """

    @property
    def name(self) -> str:
        return "morrisons"

    @property
    def limitations(self) -> list[str]:
        return [
            "Morrisons arama sayfasÄ± JavaScript render ve bot koruma gerektirir.",
            "Bot koruma sistemi aktif â€” bypass yapÄ±lmayacak.",
            "GiriÅŸ veya captcha gerektiren sayfalara eriÅŸilmeyecek.",
        ]

    def status(self) -> ProviderStatusItem:
        return self._limited_status(
            "Morrisons statik HTTP ile eriÅŸilemiyor. Bot korumaya saygÄ± gÃ¶steriliyor."
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        logger.info(f"[morrisons] Arama atlandÄ± â€” provider LIMITED: {query}")
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        logger.info("[morrisons] Fiyat alÄ±mÄ± atlandÄ± â€” provider LIMITED")
        return []
