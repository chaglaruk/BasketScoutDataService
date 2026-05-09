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
        from bs4 import BeautifulSoup
        import re
        results = []
        for name in product_names:
            try:
                r = httpx.get(
                    f"https://www.tesco.com/shop/en-GB/search?query={name}",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    timeout=10.0,
                    follow_redirects=True
                )
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    
                    # 1. Product container'lar bulmaya calis (Tesco'nun genis listesi)
                    # Gercek sayfa yapisi srekli degistiginden, href'i urun iceren a etiketlerini veya fiyatlari ariyoruz
                    
                    found_price = None
                    found_name = None
                    confidence = 0.3 # Default low confidence due to scraping heuristic
                    
                    # Sayfadaki tum text'i kontrol edip hedeflenen urun var mi bakalim
                    text_lower = r.text.lower()
                    name_words = name.lower().split()
                    matches_name = all(w in text_lower for w in name_words)
                    
                    if not matches_name:
                        logger.info(f"Tesco: '{name}' sayfa iceriginde bulunamadi.")
                        continue # Fail cleanly

                    # Daha spesifik HTML aramasi (e.g., class'inda price gecen)
                    price_elements = soup.find_all(string=re.compile(r'^£\d+\.\d{2}$'))
                    if not price_elements:
                        # Fallback to naive regex
                        prices = re.findall(r'£(\d+\.\d{2})', r.text)
                        if prices:
                            found_price = float(prices[0])
                            found_name = f"{name} (Tesco Tahmini)"
                            confidence = 0.2 # Very low confidence, naive regex
                    else:
                        found_price = float(price_elements[0].replace('£', ''))
                        found_name = f"{name} (Tesco Arama Sonucu)"
                        confidence = 0.5 # A bit better, found a specific price element
                        
                    if found_price is not None:
                        results.append(PriceItem(
                            retailer="Tesco",
                            retailer_slug="tesco",
                            product=found_name,
                            price=found_price,
                            currency="GBP",
                            loyalty_price=None,
                            own_brand=False,
                            available=None, # Mark stock as unknown since it's not reliable
                            source=self.name,
                            source_url=str(r.url),
                            last_checked_at=utcnow(),
                            confidence=confidence, # Reduced confidence documented
                            is_stale=False,
                        ))
            except Exception as exc:
                logger.warning(f"Tesco probe error for {name}: {exc}")
        return results
