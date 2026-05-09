"""ProviderRegistry — tüm provider'ları yöneten merkezi kayıt."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.providers.base import BaseProvider
from app.providers.manual_import_provider import ManualImportProvider
from app.providers.mock_provider import MockProvider
from app.providers.open_food_facts_provider import OpenFoodFactsProvider
from app.providers.open_prices_provider import OpenPricesProvider
from app.providers.retailers.aldi_provider import AldiProvider
from app.providers.retailers.asda_provider import AsdaProvider
from app.providers.retailers.coop_provider import CoopProvider
from app.providers.retailers.lidl_provider import LidlProvider
from app.providers.retailers.morrisons_provider import MorrisonsProvider
from app.providers.retailers.sainsburys_provider import SainsburysProvider
from app.providers.retailers.tesco_provider import TescoProvider
from app.providers.retailers.waitrose_provider import WaitroseProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Tüm veri provider'larının merkezi kaydı.

    - Provider'ları adına göre döndürür.
    - Her provider hatası izole edilir.
    - Varsayılan provider settings'den alınır.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._providers: dict[str, BaseProvider] = {}
        self._build()

    def _build(self) -> None:
        """Tüm provider'ları başlatır."""
        candidates: list[BaseProvider] = [
            MockProvider(),
            ManualImportProvider(),
            OpenFoodFactsProvider(),
            OpenPricesProvider(),
            TescoProvider(),
            AsdaProvider(),
            SainsburysProvider(),
            MorrisonsProvider(),
            WaitroseProvider(),
            CoopProvider(),
            AldiProvider(),
            LidlProvider(),
        ]
        for p in candidates:
            try:
                self._providers[p.name] = p
                logger.debug(f"Provider kayıt: {p.name} ({p.type})")
            except Exception as exc:
                logger.error(f"Provider başlatma hatası {p.name}: {exc}")

    def get(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def get_default(self) -> BaseProvider:
        name = self._settings.default_provider
        p = self._providers.get(name)
        if p is None:
            logger.warning(f"Varsayılan provider '{name}' bulunamadı, mock kullanılıyor.")
            return self._providers["mock"]
        return p

    def all(self) -> list[BaseProvider]:
        return list(self._providers.values())

    def all_statuses(self) -> list[ProviderStatusItem]:
        statuses: list[ProviderStatusItem] = []
        for p in self._providers.values():
            try:
                statuses.append(p.status())
            except Exception as exc:
                logger.error(f"Provider status hatası {p.name}: {exc}")
                statuses.append(
                    ProviderStatusItem(
                        name=p.name,
                        status="error",
                        type=p.type,
                        message=str(exc),
                    )
                )
        return statuses

    def search_products(
        self,
        query: str,
        provider_names: list[str] | None = None,
    ) -> list[ProductSummary]:
        """Birden fazla provider'da ürün arar, sonuçları birleştirir."""
        providers = self._select_providers(provider_names)
        results: list[ProductSummary] = []
        for p in providers:
            try:
                found = p.search_products(query)
                results.extend(found)
            except Exception as exc:
                logger.error(f"[{p.name}] search_products hatası: {exc}")
        return results

    def get_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
        provider_names: list[str] | None = None,
    ) -> list[PriceItem]:
        """Birden fazla provider'dan fiyat toplar."""
        providers = self._select_providers(provider_names)
        results: list[PriceItem] = []
        for p in providers:
            try:
                found = p.get_latest_prices(product_names, postcode=postcode)
                results.extend(found)
            except Exception as exc:
                logger.error(f"[{p.name}] get_latest_prices hatası: {exc}")
        return results

    def _select_providers(self, names: list[str] | None) -> list[BaseProvider]:
        if names:
            return [self._providers[n] for n in names if n in self._providers]
        # Varsayılan: yalnızca varsayılan provider
        return [self.get_default()]


# Singleton
_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
