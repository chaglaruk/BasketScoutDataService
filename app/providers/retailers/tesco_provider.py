"""TescoProvider - limited safe public-page price probe."""

from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.core.time import utcnow
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.retailers.scraping_base import ScrapingBaseProvider

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.tesco.com/shop/en-GB/search?query={query}"
_USER_AGENT = "BasketScoutDataService/0.1.0 (limited safe probe)"
_PRICE_RE = re.compile(r"£\s*(\d+(?:\.\d{2})?)")


class TescoProvider(ScrapingBaseProvider):
    """Limited Tesco public-page probe.

    The provider does not bypass login, captcha, bot protection or private APIs.
    It only attempts a low-volume public search page fetch. If the public HTML
    does not expose stable product/price content, it returns no prices.
    """

    @property
    def name(self) -> str:
        return "tesco"

    @property
    def supports_live_prices(self) -> bool:
        return False

    @property
    def supports_stock(self) -> bool:
        return False

    @property
    def limitations(self) -> list[str]:
        return [
            "Limited public-page probe only; not an official Tesco API.",
            "No login, captcha, private API, or bot-protection bypass is used.",
            "Search pages may be JavaScript rendered, blocked, or structurally unstable.",
            "Stock availability is not provided reliably and remains Unknown.",
        ]

    def status(self) -> ProviderStatusItem:
        return ProviderStatusItem(
            name=self.name,
            status="limited",
            type=self.type,
            last_run_at=utcnow(),
            message="Tesco limited public-page probe is available but low confidence.",
            limitations=self.limitations,
            supports_live_prices=self.supports_live_prices,
            supports_stock=self.supports_stock,
            confidence_score=0.3,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        results: list[PriceItem] = []
        for name in product_names:
            try:
                item = self._safe_probe(name)
                if item is not None:
                    results.append(item)
            except Exception as exc:
                logger.warning("Tesco limited probe failed for %s: %s", name, exc)
        return results

    def _safe_probe(self, name: str) -> PriceItem | None:
        url = _SEARCH_URL.format(query=quote_plus(name))
        response = httpx.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=10.0,
            follow_redirects=True,
        )
        if response.status_code != 200:
            logger.info("Tesco limited probe HTTP %s for %s", response.status_code, name)
            return None

        text = response.text
        normalized_text = text.lower()
        words = [word for word in name.lower().split() if len(word) > 2]
        if words and not all(word in normalized_text for word in words):
            logger.info("Tesco limited probe could not confirm product words for %s", name)
            return None

        soup = BeautifulSoup(text, "html.parser")
        visible_text = soup.get_text(" ", strip=True)
        match = _PRICE_RE.search(visible_text) or _PRICE_RE.search(text)
        if not match:
            logger.info("Tesco limited probe found no visible price for %s", name)
            return None

        price = float(match.group(1))
        return PriceItem(
            retailer="Tesco",
            retailer_slug="tesco",
            product=f"{name} (Tesco limited match)",
            price=price,
            currency="GBP",
            loyalty_price=None,
            own_brand=False,
            available=None,
            source=self.name,
            source_url=str(response.url),
            last_checked_at=utcnow(),
            confidence=0.3,
            is_stale=False,
        )
