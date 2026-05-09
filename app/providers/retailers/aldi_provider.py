"""AldiProvider â€” Aldi scraping provider."""

from __future__ import annotations

import logging

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)


class AldiProvider(ScrapingBaseProvider):
    """
    Aldi scraping provider.

    DURUM: LIMITED
    Aldi UK Ã¼rÃ¼n sayfalarÄ± dinamik render; eriÅŸim bot koruma ile sÄ±nÄ±rlÄ±dÄ±r.
    Captcha veya login bypass yapÄ±lmayacaktÄ±r.

    Gelecek geliÅŸtirme:
    - Resmi API yayÄ±nlanÄ±rsa eklenecek.
    - EriÅŸim politikasÄ± deÄŸiÅŸtirirse yeniden deÄŸerlendirilecek.
    """

    @property
    def name(self) -> str:
        return "aldi"

    @property
    def limitations(self) -> list[str]:
        return [
            "Aldi UK Ã¼rÃ¼n sayfalarÄ± dinamik render; eriÅŸim bot koruma ile sÄ±nÄ±rlÄ±dÄ±r.",
            "Bot koruma sistemi aktif â€” bypass yapÄ±lmayacak.",
            "GiriÅŸ veya captcha gerektiren sayfalara eriÅŸilmeyecek.",
        ]

    def status(self) -> ProviderStatusItem:
        return self._limited_status(
            "Aldi statik HTTP ile eriÅŸilemiyor. Bot korumaya saygÄ± gÃ¶steriliyor."
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        logger.info(f"[aldi] Arama atlandÄ± â€” provider LIMITED: {query}")
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        logger.info("[aldi] Fiyat alÄ±mÄ± atlandÄ± â€” provider LIMITED")
        return []
