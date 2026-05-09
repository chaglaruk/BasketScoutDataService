"""WaitroseProvider â€” Waitrose scraping provider."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)


class WaitroseProvider(ScrapingBaseProvider):
    """
    Waitrose scraping provider.

    DURUM: LIMITED
    Waitrose Ã¼rÃ¼n sayfalarÄ± JavaScript ile yÃ¼klenir; statik HTTP yetersiz kalÄ±r.
    Captcha veya login bypass yapÄ±lmayacaktÄ±r.

    Gelecek geliÅŸtirme:
    - Resmi API yayÄ±nlanÄ±rsa eklenecek.
    - EriÅŸim politikasÄ± deÄŸiÅŸtirirse yeniden deÄŸerlendirilecek.
    """

    @property
    def name(self) -> str:
        return "waitrose"

    @property
    def limitations(self) -> list[str]:
        return [
            "Waitrose Ã¼rÃ¼n sayfalarÄ± JavaScript ile yÃ¼klenir; statik HTTP yetersiz kalÄ±r.",
            "Bot koruma sistemi aktif â€” bypass yapÄ±lmayacak.",
            "GiriÅŸ veya captcha gerektiren sayfalara eriÅŸilmeyecek.",
        ]

    def status(self) -> ProviderStatusItem:
        return self._limited_status(
            "Waitrose statik HTTP ile eriÅŸilemiyor. Bot korumaya saygÄ± gÃ¶steriliyor."
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        logger.info(f"[waitrose] Arama atlandÄ± â€” provider LIMITED: {query}")
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        logger.info("[waitrose] Fiyat alÄ±mÄ± atlandÄ± â€” provider LIMITED")
        return []
