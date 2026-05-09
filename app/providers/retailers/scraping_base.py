"""ScrapingBaseProvider — HTTP tabanlı scraping provider'ları için ortak altyapı."""

from __future__ import annotations

import logging
import time

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.time import utcnow
from app.domain.models import ProviderStatusItem
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ScrapingBaseProvider(BaseProvider):
    """
    HTTP scraping provider'ları için temel sınıf.

    Politika:
    - Giriş gerektiren sayfaları scrape ETME.
    - Captcha'yı bypass ETME.
    - Bot korumasını atlatma girişiminde BULUNMA.
    - Minimum istek aralığına uy (rate_limit_seconds).
    - robots.txt'e saygı göster.
    - Hataları sessizce logla, diğer provider'ları etkileme.
    """

    _last_request_time: float = 0.0

    def __init__(self) -> None:
        settings = get_settings()
        self._rate_limit = settings.scraping_rate_limit_seconds
        self._client = httpx.Client(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; BasketScoutBot/0.1; "
                    "+https://github.com/chaglaruk/BasketScoutDataService)"
                ),
                "Accept-Language": "en-GB,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            follow_redirects=True,
            timeout=15.0,
        )

    def _rate_limited_get(self, url: str, **kwargs) -> httpx.Response | None:
        """Rate-limited GET isteği yapar."""
        elapsed = time.monotonic() - ScrapingBaseProvider._last_request_time
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        try:
            ScrapingBaseProvider._last_request_time = time.monotonic()
            r = self._client.get(url, **kwargs)
            return r
        except httpx.HTTPError as exc:
            logger.warning(f"[{self.name}] HTTP hatası {url}: {exc}")
            return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @property
    def type(self) -> str:
        return "scraping"

    @property
    def supports_live_prices(self) -> bool:
        return False  # Alt sınıf override edebilir, yalnızca doğrulandığında

    @property
    def requires_postcode(self) -> bool:
        return False

    def _blocked_status(self, reason: str) -> ProviderStatusItem:
        return ProviderStatusItem(
            name=self.name,
            status="blocked",
            type=self.type,
            last_run_at=utcnow(),
            message=reason,
            limitations=self.limitations,
        )

    def _limited_status(self, reason: str) -> ProviderStatusItem:
        return ProviderStatusItem(
            name=self.name,
            status="limited",
            type=self.type,
            last_run_at=utcnow(),
            message=reason,
            limitations=self.limitations,
        )
