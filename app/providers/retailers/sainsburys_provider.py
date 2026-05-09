"""Sainsbury'sProvider â€” Sainsbury's scraping provider."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)


class SainsburysProvider(ScrapingBaseProvider):
    """
    Sainsbury's scraping provider.

    DURUM: LIMITED
    Sainsbury's Ã¼rÃ¼n arama API'si herkese aÃ§Ä±k deÄŸil; statik HTML eriÅŸimi kÄ±sÄ±tlÄ±dÄ±r.
    Captcha veya login bypass yapÄ±lmayacaktÄ±r.

    Gelecek geliÅŸtirme:
    - Resmi API yayÄ±nlanÄ±rsa eklenecek.
    - EriÅŸim politikasÄ± deÄŸiÅŸtirirse yeniden deÄŸerlendirilecek.
    """

    @property
    def name(self) -> str:
        return "sainsburys"

    @property
    def limitations(self) -> list[str]:
        return [
            "Sainsbury's Ã¼rÃ¼n arama API'si herkese aÃ§Ä±k deÄŸil; statik HTML eriÅŸimi kÄ±sÄ±tlÄ±dÄ±r.",
            "Bot koruma sistemi aktif â€” bypass yapÄ±lmayacak.",
            "GiriÅŸ veya captcha gerektiren sayfalara eriÅŸilmeyecek.",
        ]

    def status(self) -> ProviderStatusItem:
        return self._limited_status(
            "Sainsbury's statik HTTP ile eriÅŸilemiyor. Bot korumaya saygÄ± gÃ¶steriliyor."
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        logger.info(f"[sainsburys] Arama atlandÄ± â€” provider LIMITED: {query}")
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        logger.info("[sainsburys] Fiyat alÄ±mÄ± atlandÄ± â€” provider LIMITED")
        return []
