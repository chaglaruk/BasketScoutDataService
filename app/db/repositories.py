"""Veritabanı repository sınıfları — sorgu mantığı."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    PriceSnapshot,
    Product,
    ProductAlias,
    ProviderRun,
    Retailer,
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
