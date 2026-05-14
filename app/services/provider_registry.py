"""ProviderRegistry â€” tÃ¼m provider'larÄ± yÃ¶neten merkezi kayÄ±t."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import get_settings
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.domain.normalization import normalize_name, similarity_score
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
from app.providers.scrapling_observation_provider import ScraplingObservationProvider
from app.providers.web_observation_provider import WebObservationProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderPriceResult:
    items: list[PriceItem]
    why_mock_used: str | None = None


class ProviderRegistry:
    """
    TÃ¼m veri provider'larÄ±nÄ±n merkezi kaydÄ±.

    - Provider'larÄ± adÄ±na gÃ¶re dÃ¶ndÃ¼rÃ¼r.
    - Her provider hatasÄ± izole edilir.
    - VarsayÄ±lan provider settings'den alÄ±nÄ±r.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._providers: dict[str, BaseProvider] = {}
        self._build()

    def _build(self) -> None:
        """TÃ¼m provider'larÄ± baÅŸlatÄ±r."""
        candidates: list[BaseProvider] = [
            ManualImportProvider(),
            WebObservationProvider(),
            ScraplingObservationProvider(),
            OpenPricesProvider(),
            TescoProvider(),
            OpenFoodFactsProvider(),
            AsdaProvider(),
            SainsburysProvider(),
            MorrisonsProvider(),
            WaitroseProvider(),
            CoopProvider(),
            AldiProvider(),
            LidlProvider(),
            MockProvider(),
        ]
        for p in candidates:
            try:
                self._providers[p.name] = p
                logger.debug(f"Provider kayÄ±t: {p.name} ({p.type})")
            except Exception as exc:
                logger.error(f"Provider baÅŸlatma hatasÄ± {p.name}: {exc}")

    def get(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def get_default(self) -> BaseProvider:
        name = self._settings.default_provider
        p = self._providers.get(name)
        if p is None:
            logger.warning(f"VarsayÄ±lan provider '{name}' bulunamadÄ±, mock kullanÄ±lÄ±yor.")
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
                logger.error(f"Provider status hatasÄ± {p.name}: {exc}")
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
        """Birden fazla provider'da Ã¼rÃ¼n arar, sonuÃ§larÄ± birleÅŸtirir."""
        providers = self._select_providers(provider_names)
        results: list[ProductSummary] = []
        for p in providers:
            try:
                found = p.search_products(query)
                results.extend(found)
            except Exception as exc:
                logger.error(f"[{p.name}] search_products hatasÄ±: {exc}")
        return results

    def get_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
        provider_names: list[str] | None = None,
    ) -> list[PriceItem]:
        """Birden fazla provider'dan fiyat toplar."""
        return self.get_prices_with_metadata(product_names, postcode, provider_names).items

    def get_prices_with_metadata(
        self,
        product_names: list[str],
        postcode: str | None = None,
        provider_names: list[str] | None = None,
    ) -> ProviderPriceResult:
        """Fiyatlari toplar ve mock fallback nedenini metadata olarak tasir."""
        providers = self._select_providers(provider_names)
        results: list[PriceItem] = []

        if provider_names:
            for p in providers:
                try:
                    found = p.get_latest_prices(product_names, postcode=postcode)
                    results.extend(found)
                except Exception as exc:
                    logger.error(f"[{p.name}] get_latest_prices error: {exc}")
            return ProviderPriceResult(items=results)

        remaining = list(dict.fromkeys(product_names))
        mock_provider: BaseProvider | None = None

        for p in providers:
            if p.name == "mock":
                mock_provider = p
                continue
            if not remaining:
                break
            try:
                found = p.get_latest_prices(remaining, postcode=postcode)
                results.extend(found)
                remaining = [
                    query
                    for query in remaining
                    if not any(_price_matches_query(query, item) for item in found)
                ]
            except Exception as exc:
                logger.error(f"[{p.name}] get_latest_prices error: {exc}")

        why_mock_used: str | None = None
        if remaining and mock_provider is not None:
            try:
                mock_found = mock_provider.get_latest_prices(remaining, postcode=postcode)
                results.extend(mock_found)
                joined = ", ".join(remaining)
                why_mock_used = (
                    f"No manual/open/limited provider data for: {joined}. "
                    "Using offline demo prices only for those unresolved items."
                )
                if not mock_found:
                    why_mock_used = (
                        f"No provider data found for: {joined}. "
                        "Offline demo fallback also had no matching product."
                    )
            except Exception as exc:
                logger.error(f"[mock] get_latest_prices error: {exc}")
                why_mock_used = f"Mock fallback failed for unresolved items: {exc}"

        return ProviderPriceResult(items=results, why_mock_used=why_mock_used)

    def _select_providers(self, names: list[str] | None) -> list[BaseProvider]:
        if names:
            return [self._providers[n] for n in names if n in self._providers]

        # Priority order for default comparison
        priority_order = ["manual_import", "web_observation", "open_prices", "tesco", "mock"]
        selected = []
        for name in priority_order:
            if name in self._providers:
                selected.append(self._providers[name])
        return selected


def _price_matches_query(query: str, item: PriceItem) -> bool:
    normalized_query = normalize_name(query)
    normalized_product = normalize_name(item.product)
    return (
        normalized_query in normalized_product
        or normalized_product in normalized_query
        or similarity_score(normalized_query, normalized_product) >= 0.3
    )


# Singleton
_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
