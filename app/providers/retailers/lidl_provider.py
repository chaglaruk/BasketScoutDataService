"""LidlProvider â€” Lidl scraping provider."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)


class LidlProvider(ScrapingBaseProvider):
    """
    Lidl scraping provider.

    DURUM: LIMITED
    Lidl GB Ã¼rÃ¼n arama JavaScript ile Ã§alÄ±ÅŸÄ±r; statik HTTP yetersizdir.
    Captcha veya login bypass yapÄ±lmayacaktÄ±r.

    Gelecek geliÅŸtirme:
    - Resmi API yayÄ±nlanÄ±rsa eklenecek.
    - EriÅŸim politikasÄ± deÄŸiÅŸtirirse yeniden deÄŸerlendirilecek.
    """

    @property
    def name(self) -> str:
        return "lidl"

    @property
    def limitations(self) -> list[str]:
        return [
            "Lidl GB Ã¼rÃ¼n arama JavaScript ile Ã§alÄ±ÅŸÄ±r; statik HTTP yetersizdir.",
            "Bot koruma sistemi aktif â€” bypass yapÄ±lmayacak.",
            "GiriÅŸ veya captcha gerektiren sayfalara eriÅŸilmeyecek.",
        ]

    def status(self) -> ProviderStatusItem:
        return self._limited_status(
            "Lidl statik HTTP ile eriÅŸilemiyor. Bot korumaya saygÄ± gÃ¶steriliyor."
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        logger.info(f"[lidl] Arama atlandÄ± â€” provider LIMITED: {query}")
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        logger.info("[lidl] Fiyat alÄ±mÄ± atlandÄ± â€” provider LIMITED")
        return []
