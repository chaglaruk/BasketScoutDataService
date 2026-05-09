"""OpenPricesProvider — açık/kitlesel kaynaklı fiyat verileri."""

from __future__ import annotations

import logging

import httpx

from app.core.time import utcnow
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Open Prices API — https://prices.openfoodfacts.org
_BASE_URL = "https://prices.openfoodfacts.org/api/v1"


class OpenPricesProvider(BaseProvider):
    """
    Open Prices (prices.openfoodfacts.org) — kitlesel kaynaklı fiyat verileri.

    SINIRLILIKLAR:
    - Resmi süpermarket fiyatı DEĞİLDİR.
    - Kullanıcı tarafından girilen veriler — yanlış veya eski olabilir.
    - Güven skoru 0.6 tavanla sınırlandırılmıştır.
    - İngiltere kapsamı sınırlıdır.
    - Stok bilgisi sunmaz.
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=_BASE_URL,
            timeout=10.0,
            headers={"User-Agent": "BasketScoutDataService/0.1.0"},
        )

    @property
    def name(self) -> str:
        return "open_prices"

    @property
    def type(self) -> str:
        return "open_data"

    @property
    def supports_live_prices(self) -> bool:
        return False  # Kitlesel kaynak, resmi canlı fiyat değil

    @property
    def limitations(self) -> list[str]:
        return [
            "Kitlesel kaynaklı veri — resmi fiyat garantisi yok.",
            "Güven skoru maksimum 0.6 ile sınırlıdır.",
            "İngiltere kapsamı sınırlıdır.",
            "Stok bilgisi sunmaz.",
            "İnternet bağlantısı gerektirir.",
        ]

    def status(self) -> ProviderStatusItem:
        # Durum kontrolü için canlı HTTP probe yapmıyoruz — her çağrıda gecikme yaratır.
        return ProviderStatusItem(
            name=self.name,
            status="limited",
            type=self.type,
            last_run_at=utcnow(),
            message="Open Prices MVP iskeleti hazir. (Barkod entegrasyonu gerekli)",
            limitations=self.limitations,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        """Open Prices ürün arama desteği yoktur; boş liste döner."""
        return []

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        """
        Barkod ile fiyat arar. Ürün isimlerini barkoda dönüştürmek için
        Open Food Facts entegrasyonu gerekir — bu MVP'de skeleton olarak bırakılmıştır.
        """
        logger.info("OpenPrices: MVP'de yalnızca iskelet — barkod entegrasyonu gerekli.")
        return []
