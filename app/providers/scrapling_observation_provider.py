"""Provider for eligible Scrapling observations."""

from __future__ import annotations

import json

from app.core.config import get_settings
from app.db.database import SessionLocal, get_engine
from app.db.repositories import PriceObservationRepository, ProviderRunRepository
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.domain.normalization import normalize_name, similarity_score
from app.providers.base import BaseProvider
from app.services.scrapling_price_observation_service import get_scrapling_runtime


class ScraplingObservationProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "scrapling_observation"

    @property
    def type(self) -> str:
        return "web_observation"

    @property
    def supports_live_prices(self) -> bool:
        return False

    @property
    def supports_stock(self) -> bool:
        return False

    @property
    def limitations(self) -> list[str]:
        return [
            "Safe mode only: exact watchlist URL and public pages.",
            "No login/captcha/proxy/stealth bypass.",
            "Stock remains Unknown.",
            "Not guaranteed live price.",
        ]

    def status(self) -> ProviderStatusItem:
        settings = get_settings()
        scrapling_available, fetcher_available, dynamic_available, stealthy_available, err = (
            get_scrapling_runtime()
        )
        SessionLocal.configure(bind=get_engine())
        db = SessionLocal()
        try:
            run_repo = ProviderRunRepository(db)
            last_run = run_repo.get_last_for_provider("daily_scrapling_observation")
            if not settings.scrapling_enabled:
                return ProviderStatusItem(
                    name=self.name,
                    status="limited",
                    type=self.type,
                    message="Scrapling provider disabled by configuration.",
                    limitations=self.limitations,
                    supports_live_prices=False,
                    supports_stock=False,
                    requires_postcode=False,
                )
            if not scrapling_available:
                return ProviderStatusItem(
                    name=self.name,
                    status="limited",
                    type=self.type,
                    message=f"Scrapling parser unavailable: {err}",
                    limitations=self.limitations,
                    supports_live_prices=False,
                    supports_stock=False,
                    requires_postcode=False,
                )

            extra = {
                "scrapling_available": scrapling_available,
                "fetcher_available": fetcher_available,
                "dynamic_fetcher_available": dynamic_available,
                "stealthy_fetcher_available": stealthy_available,
                "scrapling_network_enabled": settings.scrapling_network_enabled,
            }
            if last_run is None:
                return ProviderStatusItem(
                    name=self.name,
                    status="limited",
                    type=self.type,
                    message=f"No Scrapling daily run yet. runtime={json.dumps(extra)}",
                    limitations=self.limitations,
                    supports_live_prices=False,
                    supports_stock=False,
                    confidence_score=0.5,
                    requires_postcode=False,
                )

            mapped_status = "ok" if last_run.status == "success" else "limited"
            message = f"{last_run.message or ''} runtime={json.dumps(extra)}"
            return ProviderStatusItem(
                name=self.name,
                status=mapped_status,
                type=self.type,
                last_run_at=last_run.finished_at or last_run.started_at,
                message=message.strip(),
                limitations=self.limitations,
                supports_live_prices=False,
                supports_stock=False,
                confidence_score=0.5,
                requires_postcode=False,
            )
        finally:
            db.close()

    def search_products(self, query: str) -> list[ProductSummary]:
        query_norm = normalize_name(query)
        SessionLocal.configure(bind=get_engine())
        db = SessionLocal()
        try:
            rows = PriceObservationRepository(db).get_recent_public_success()
            seen: set[str] = set()
            items: list[ProductSummary] = []
            for row in rows:
                if not row.provider_used.startswith("scrapling_observation_"):
                    continue
                product_norm = normalize_name(row.canonical_product_name)
                if query_norm not in product_norm and similarity_score(query_norm, product_norm) < 0.4:
                    continue
                if row.canonical_product_name in seen:
                    continue
                seen.add(row.canonical_product_name)
                items.append(
                    ProductSummary(
                        id=row.id,
                        canonical_name=row.canonical_product_name,
                        source="Observed web price",
                        confidence=min(max(row.confidence_score, 0.0), 1.0),
                    )
                )
            return items[:20]
        finally:
            db.close()

    def get_latest_prices(self, product_names: list[str], postcode: str | None = None) -> list[PriceItem]:
        del postcode
        normalized_queries = [normalize_name(name) for name in product_names if name.strip()]
        if not normalized_queries:
            return []

        SessionLocal.configure(bind=get_engine())
        db = SessionLocal()
        try:
            rows = PriceObservationRepository(db).get_recent_public_success()
            matched: dict[tuple[str, str], PriceItem] = {}
            for row in rows:
                if not row.provider_used.startswith("scrapling_observation_"):
                    continue
                if row.price_amount is None:
                    continue
                product_norm = normalize_name(row.canonical_product_name)
                matches_query = False
                for query_norm in normalized_queries:
                    if (
                        query_norm in product_norm
                        or product_norm in query_norm
                        or similarity_score(query_norm, product_norm) >= 0.35
                    ):
                        matches_query = True
                        break
                if not matches_query:
                    continue
                key = (row.retailer_slug, row.canonical_product_name)
                if key in matched:
                    continue
                matched[key] = PriceItem(
                    retailer=row.retailer_name,
                    retailer_slug=row.retailer_slug,
                    product=row.canonical_product_name,
                    price=row.price_amount,
                    currency=row.currency,
                    loyalty_price=row.loyalty_price_amount,
                    own_brand=False,
                    available=None,
                    raw_availability_text="Stock status unknown",
                    source="Observed web price",
                    source_url=row.source_url,
                    last_checked_at=row.observed_at,
                    confidence=min(max(row.confidence_score, 0.0), 1.0),
                    is_stale=False,
                )
            return list(matched.values())
        finally:
            db.close()

