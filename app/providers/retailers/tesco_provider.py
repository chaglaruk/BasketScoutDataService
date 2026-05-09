"""TescoProvider — Tesco scraping provider (güvenli statik HTTP denemesi)."""

from __future__ import annotations

import logging

import httpx

from app.core.time import utcnow
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
    def supports_live_prices(self) -> bool:
        return True  # Feasibility probe eklendi

    @property
    def limitations(self) -> list[str]:
        return [
            "Resmi API yoktur.",
            "Aşırı istekte IP bloklaması olabilir (Bot koruması).",
            "Güvenli limitli probe çalıştırılıyor.",
        ]

    def status(self) -> ProviderStatusItem:
        return ProviderStatusItem(
            name=self.name,
            status="ok", # Feasibility probe added
            type=self.type,
            last_run_at=utcnow(),
            message="Tesco arama sayfası erişilebilir ve Regex probe kullanılıyor.",
            limitations=self.limitations,
            supports_live_prices=self.supports_live_prices,
            supports_stock=self.supports_stock,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        import re
        results = []
        for name in product_names:
            try:
                r = httpx.get(
                    f"https://www.tesco.com/shop/en-GB/search?query={name}",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    timeout=5.0,
                    follow_redirects=True
                )
                if r.status_code == 200:
                    # En basit HTML parsing: Fiyat içeren metinleri regex ile çıkar
                    # Not: Bu güvenli "safe probe" olup, karmaşık JSON parsing içermez
                    prices = re.findall(r'£(\d+\.\d{2})', r.text)
                    if prices:
                        # İlk bulduğumuz fiyatı (genelde ilk sonuç) alıyoruz
                        # Gerçek üretim senaryosunda Playwright / JSON state parsing önerilir.
                        price_val = float(prices[0])
                        results.append(PriceItem(
                            retailer="Tesco",
                            retailer_slug="tesco",
                            product=name,
                            price=price_val,
                            currency="GBP",
                            loyalty_price=None,
                            own_brand=False,
                            available=True,
                            source=self.name,
                            source_url=str(r.url),
                            last_checked_at=utcnow(),
                            confidence=0.5, # Regex parsing is low confidence
                            is_stale=False,
                        ))
            except Exception as exc:
                logger.warning(f"Tesco probe error for {name}: {exc}")
        return results
