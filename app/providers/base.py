"""Provider temel sınıfı — tüm provider'lar bu ABC'yi uygular."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem


class BaseProvider(ABC):
    """
    Tüm veri provider'larının temel sınıfı.

    Her provider:
    - Yalnızca kendi veri kaynağından sorumludur
    - Hatalarını sessizce loglar, yayılmasına izin vermez
    - Canlı fiyat veya stok desteğini açıkça belirtir
    - Sınırlılıklarını belgeler
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider'ın benzersiz kısa adı."""
        ...

    @property
    @abstractmethod
    def type(self) -> str:
        """Provider tipi: mock | manual | open_data | scraping."""
        ...

    @property
    def supports_live_prices(self) -> bool:
        """Provider canlı fiyat verisi sunuyorsa True."""
        return False

    @property
    def supports_stock(self) -> bool:
        """Provider stok bilgisi sunuyorsa True."""
        return False

    @property
    def requires_postcode(self) -> bool:
        """Doğru sonuçlar için posta kodu gerekiyorsa True."""
        return False

    @property
    def limitations(self) -> list[str]:
        """Bu provider'ın bilinen sınırlılıklarının listesi."""
        return []

    @abstractmethod
    def status(self) -> ProviderStatusItem:
        """Provider'ın güncel durumunu döndürür."""
        ...

    @abstractmethod
    def search_products(self, query: str) -> list[ProductSummary]:
        """Sorguyla eşleşen ürünleri arar."""
        ...

    @abstractmethod
    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        """Verilen ürün isimleri için en güncel fiyatları döndürür."""
        ...

    def refresh_products(
        self,
        product_names: list[str] | None = None,
        postcode: str | None = None,
    ) -> dict[str, Any]:
        """
        Ürün verilerini günceller.
        Alt sınıflar override edebilir; varsayılan no-op.
        """
        return {"provider": self.name, "status": "skipped", "reason": "refresh not implemented"}
