"""Veritabanı repository sınıfları — sorgu mantığı."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    PriceObservation,
    PriceSnapshot,
    Product,
    ProductAlias,
    ProviderRun,
    Retailer,
    WebPriceWatchlist,
)

# ── Retailer ──────────────────────────────────────────────────────────────────


class RetailerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Retailer]:
        return list(self.db.scalars(select(Retailer)))

    def get_by_slug(self, slug: str) -> Retailer | None:
        return self.db.scalar(select(Retailer).where(Retailer.slug == slug))

    def upsert(
        self, name: str, slug: str, website_url: str | None = None, provider_status: str = "unknown"
    ) -> Retailer:
        r = self.get_by_slug(slug)
        if r is None:
            r = Retailer(
                name=name, slug=slug, website_url=website_url, provider_status=provider_status
            )
            self.db.add(r)
            self.db.flush()
        else:
            r.provider_status = provider_status
        return r


# ── Product ───────────────────────────────────────────────────────────────────


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def search_by_name(self, query: str, limit: int = 20) -> list[Product]:
        """Canonical isim veya alias ile ürün arar."""
        normalized = query.strip().lower()
        # Alias tablosunda ara
        alias_ids = list(
            self.db.scalars(
                select(ProductAlias.product_id).where(
                    ProductAlias.normalized_alias.contains(normalized)
                )
            )
        )
        # Canonical isimde ara
        direct = list(
            self.db.scalars(
                select(Product).where(Product.normalized_name.contains(normalized)).limit(limit)
            )
        )
        direct_ids = {p.id for p in direct}
        # Alias eşleşmelerini ekle
        if alias_ids:
            extra = list(
                self.db.scalars(
                    select(Product)
                    .where(
                        Product.id.in_(alias_ids),
                        Product.id.notin_(direct_ids),
                    )
                    .limit(limit - len(direct))
                )
            )
            direct.extend(extra)
        return direct[:limit]

    def get_or_create(
        self, canonical_name: str, normalized_name: str, category: str | None = None
    ) -> Product:
        p = self.db.scalar(select(Product).where(Product.normalized_name == normalized_name))
        if p is None:
            p = Product(
                canonical_name=canonical_name,
                normalized_name=normalized_name,
                category=category,
            )
            self.db.add(p)
            self.db.flush()
        return p


# ── PriceSnapshot ─────────────────────────────────────────────────────────────


class PriceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_for_products(
        self,
        product_ids: list[int],
        retailer_ids: list[int] | None = None,
    ) -> list[PriceSnapshot]:
        """Her ürün/perakendeci çifti için en son fiyat snapshot'ını döndürür."""
        stmt = (
            select(PriceSnapshot)
            .where(PriceSnapshot.product_id.in_(product_ids))
            .order_by(PriceSnapshot.last_checked_at.desc())
        )
        if retailer_ids:
            stmt = stmt.where(PriceSnapshot.retailer_id.in_(retailer_ids))
        return list(self.db.scalars(stmt))

    def add_snapshot(self, snapshot: PriceSnapshot) -> PriceSnapshot:
        self.db.add(snapshot)
        self.db.flush()
        return snapshot


# ── ProviderRun ───────────────────────────────────────────────────────────────


class ProviderRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, provider_name: str, provider_type: str, started_at: datetime) -> ProviderRun:
        run = ProviderRun(
            provider_name=provider_name,
            provider_type=provider_type,
            status="running",
            started_at=started_at,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def finish(
        self,
        run: ProviderRun,
        status: str,
        finished_at: datetime,
        products_checked: int = 0,
        prices_found: int = 0,
        errors_count: int = 0,
        message: str | None = None,
    ) -> ProviderRun:
        run.status = status
        run.finished_at = finished_at
        run.products_checked = products_checked
        run.prices_found = prices_found
        run.errors_count = errors_count
        run.message = message
        self.db.flush()
        return run

    def get_recent(self, limit: int = 50) -> list[ProviderRun]:
        return list(
            self.db.scalars(
                select(ProviderRun).order_by(ProviderRun.started_at.desc()).limit(limit)
            )
        )

    def get_last_for_provider(self, provider_name: str) -> ProviderRun | None:
        return self.db.scalar(
            select(ProviderRun)
            .where(ProviderRun.provider_name == provider_name)
            .order_by(ProviderRun.started_at.desc())
            .limit(1)
        )


class WebPriceWatchlistRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[WebPriceWatchlist]:
        return list(self.db.scalars(select(WebPriceWatchlist).order_by(WebPriceWatchlist.id.asc())))

    def get_enabled(self) -> list[WebPriceWatchlist]:
        return list(
            self.db.scalars(
                select(WebPriceWatchlist)
                .where(WebPriceWatchlist.enabled.is_(True))
                .order_by(WebPriceWatchlist.id.asc())
            )
        )

    def count_enabled(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(WebPriceWatchlist).where(
                    WebPriceWatchlist.enabled.is_(True)
                )
            )
            or 0
        )

    def count_with_url(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(WebPriceWatchlist).where(
                    WebPriceWatchlist.product_url.is_not(None),
                    WebPriceWatchlist.product_url != "",
                )
            )
            or 0
        )

    def count_missing_url(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(WebPriceWatchlist).where(
                    (WebPriceWatchlist.product_url.is_(None)) | (WebPriceWatchlist.product_url == "")
                )
            )
            or 0
        )

    def get_recent_attempts(self, limit: int = 10) -> list[WebPriceWatchlist]:
        return list(
            self.db.scalars(
                select(WebPriceWatchlist)
                .where(WebPriceWatchlist.last_attempt_at.is_not(None))
                .order_by(WebPriceWatchlist.last_attempt_at.desc())
                .limit(limit)
            )
        )

    def upsert(
        self,
        retailer_slug: str,
        retailer_name: str,
        canonical_product_name: str,
        product_url: str | None,
        expected_product_keywords: str | None,
        enabled: bool,
        max_frequency_hours: int = 24,
        policy_status: str = "unconfigured",
        public_display_allowed: bool = False,
        notes: str | None = None,
    ) -> WebPriceWatchlist:
        row = self.db.scalar(
            select(WebPriceWatchlist).where(
                WebPriceWatchlist.retailer_slug == retailer_slug,
                WebPriceWatchlist.canonical_product_name == canonical_product_name,
            )
        )
        if row is None:
            row = WebPriceWatchlist(
                retailer_slug=retailer_slug,
                retailer_name=retailer_name,
                canonical_product_name=canonical_product_name,
                product_url=product_url,
                expected_product_keywords=expected_product_keywords,
                enabled=enabled,
                max_frequency_hours=max_frequency_hours,
                policy_status=policy_status,
                public_display_allowed=public_display_allowed,
                notes=notes,
            )
            self.db.add(row)
            self.db.flush()
            return row

        row.retailer_name = retailer_name
        row.product_url = product_url
        row.expected_product_keywords = expected_product_keywords
        row.enabled = enabled
        row.max_frequency_hours = max_frequency_hours
        row.policy_status = policy_status
        row.public_display_allowed = public_display_allowed
        row.notes = notes
        self.db.flush()
        return row


class PriceObservationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, item: PriceObservation) -> PriceObservation:
        self.db.add(item)
        self.db.flush()
        return item

    def latest_public_for_product_names(self, product_names: list[str]) -> list[PriceObservation]:
        if not product_names:
            return []
        lowered = [name.strip().lower() for name in product_names if name.strip()]
        if not lowered:
            return []
        rows = list(
            self.db.scalars(
                select(PriceObservation)
                .where(
                    PriceObservation.outcome_status == "SUCCESS",
                    PriceObservation.public_display_allowed.is_(True),
                    PriceObservation.stock_status == "Unknown",
                )
                .order_by(PriceObservation.observed_at.desc())
            )
        )
        best: dict[tuple[str, str], PriceObservation] = {}
        for row in rows:
            canonical = row.canonical_product_name.strip().lower()
            if canonical not in lowered:
                continue
            key = (row.retailer_slug, canonical)
            if key not in best:
                best[key] = row
        return list(best.values())

    def get_recent_public_success(self, limit: int = 500) -> list[PriceObservation]:
        return list(
            self.db.scalars(
                select(PriceObservation)
                .where(
                    PriceObservation.outcome_status == "SUCCESS",
                    PriceObservation.public_display_allowed.is_(True),
                    PriceObservation.stock_status == "Unknown",
                )
                .order_by(PriceObservation.observed_at.desc())
                .limit(limit)
            )
        )

    def get_recent_success(self, limit: int = 10) -> list[PriceObservation]:
        return list(
            self.db.scalars(
                select(PriceObservation)
                .where(PriceObservation.outcome_status == "SUCCESS")
                .order_by(PriceObservation.observed_at.desc())
                .limit(limit)
            )
        )

    def count_internal_only_from_run(self, run_id: int) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(PriceObservation)
                .where(
                    PriceObservation.run_id == run_id,
                    PriceObservation.outcome_status == "SUCCESS",
                    PriceObservation.public_display_allowed.is_(False),
                )
            )
            or 0
        )
