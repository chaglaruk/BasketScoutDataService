"""Co-opProvider â€” Co-op scraping provider."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)


class CoopProvider(ScrapingBaseProvider):
    """
    Co-op scraping provider.

    DURUM: LIMITED
    Co-op online maÄŸaza statik HTTP ile eriÅŸilebilir deÄŸil; Playwright gerektirir.
    Captcha veya login bypass yapÄ±lmayacaktÄ±r.

    Gelecek geliÅŸtirme:
    - Resmi API yayÄ±nlanÄ±rsa eklenecek.
    - EriÅŸim politikasÄ± deÄŸiÅŸtirirse yeniden deÄŸerlendirilecek.
    """

    @property
    def name(self) -> str:
        return "coop"

    @property
    def limitations(self) -> list[str]:
        return [
            "Co-op online maÄŸaza statik HTTP ile eriÅŸilebilir deÄŸil; Playwright gerektirir.",
            "Bot koruma sistemi aktif â€” bypass yapÄ±lmayacak.",
            "GiriÅŸ veya captcha gerektiren sayfalara eriÅŸilmeyecek.",
        ]

    def status(self) -> ProviderStatusItem:
        return self._limited_status(
            "Co-op statik HTTP ile eriÅŸilemiyor. Bot korumaya saygÄ± gÃ¶steriliyor."
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        logger.info(f"[coop] Arama atlandÄ± â€” provider LIMITED: {query}")
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        logger.info("[coop] Fiyat alÄ±mÄ± atlandÄ± â€” provider LIMITED")
        return []
