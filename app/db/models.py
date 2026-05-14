"""SQLAlchemy ORM modelleri — veritabanı tabloları."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Retailer(Base):
    __tablename__ = "retailer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    website_url: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(10), default="GB")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    provider_status: Mapped[str] = mapped_column(String(20), default="unknown")
    # ok | limited | blocked | unknown

    price_snapshots: Mapped[list[PriceSnapshot]] = relationship(
        "PriceSnapshot", back_populates="retailer"
    )
    availability_snapshots: Mapped[list[AvailabilitySnapshot]] = relationship(
        "AvailabilitySnapshot", back_populates="retailer"
    )
    store_locations: Mapped[list[StoreLocation]] = relationship(
        "StoreLocation", back_populates="retailer"
    )


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    brand: Mapped[str | None] = mapped_column(String(100))
    barcode: Mapped[str | None] = mapped_column(String(50), index=True)
    size_text: Mapped[str | None] = mapped_column(String(50))
    unit: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    aliases: Mapped[list[ProductAlias]] = relationship(
        "ProductAlias", back_populates="product", cascade="all, delete-orphan"
    )
    price_snapshots: Mapped[list[PriceSnapshot]] = relationship(
        "PriceSnapshot", back_populates="product"
    )
    availability_snapshots: Mapped[list[AvailabilitySnapshot]] = relationship(
        "AvailabilitySnapshot", back_populates="product"
    )


class ProductAlias(Base):
    __tablename__ = "product_alias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")

    product: Mapped[Product] = relationship("Product", back_populates="aliases")


class StoreLocation(Base):
    __tablename__ = "store_location"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retailer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("retailer.id"), nullable=False, index=True
    )
    postcode: Mapped[str | None] = mapped_column(String(20), index=True)
    store_name: Mapped[str | None] = mapped_column(String(150))
    store_id: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    retailer: Mapped[Retailer] = relationship("Retailer", back_populates="store_locations")
    price_snapshots: Mapped[list[PriceSnapshot]] = relationship(
        "PriceSnapshot", back_populates="store_location"
    )


class PriceSnapshot(Base):
    __tablename__ = "price_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retailer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("retailer.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.id"), nullable=False, index=True
    )
    store_location_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("store_location.id"))
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    unit_price: Mapped[float | None] = mapped_column(Float)
    unit_price_unit: Mapped[str | None] = mapped_column(String(30))
    loyalty_price: Mapped[float | None] = mapped_column(Float)
    own_brand: Mapped[bool] = mapped_column(Boolean, default=False)
    available: Mapped[bool | None] = mapped_column(Boolean)
    raw_availability_text: Mapped[str | None] = mapped_column(String(100))
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    retailer: Mapped[Retailer] = relationship("Retailer", back_populates="price_snapshots")
    product: Mapped[Product] = relationship("Product", back_populates="price_snapshots")
    store_location: Mapped[StoreLocation | None] = relationship(
        "StoreLocation", back_populates="price_snapshots"
    )


class AvailabilitySnapshot(Base):
    __tablename__ = "availability_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retailer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("retailer.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.id"), nullable=False, index=True
    )
    store_location_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("store_location.id"))
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    available: Mapped[bool | None] = mapped_column(Boolean)
    raw_status: Mapped[str | None] = mapped_column(String(100))
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    retailer: Mapped[Retailer] = relationship("Retailer", back_populates="availability_snapshots")
    product: Mapped[Product] = relationship("Product", back_populates="availability_snapshots")


class ProviderRun(Base):
    __tablename__ = "provider_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # success | partial | failed | running
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    products_checked: Mapped[int] = mapped_column(Integer, default=0)
    prices_found: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text)


class WebPriceWatchlist(Base):
    __tablename__ = "web_price_watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retailer_slug: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    retailer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    canonical_product_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    product_url: Mapped[str | None] = mapped_column(Text)
    expected_product_keywords: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_frequency_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    robots_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    policy_status: Mapped[str] = mapped_column(String(40), default="unconfigured", nullable=False)
    public_display_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PriceObservation(Base):
    __tablename__ = "price_observation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watchlist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("web_price_watchlist.id"), nullable=False, index=True
    )
    run_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("provider_run.id"), index=True)
    retailer_slug: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    retailer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    canonical_product_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    raw_product_name: Mapped[str | None] = mapped_column(String(255))
    price_amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)
    loyalty_price_amount: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider_used: Mapped[str] = mapped_column(String(80), nullable=False)
    data_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    freshness_bucket: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    stock_status: Mapped[str] = mapped_column(String(30), default="Unknown", nullable=False)
    warnings: Mapped[str | None] = mapped_column(Text)
    parser_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    public_display_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rights_status: Mapped[str] = mapped_column(String(40), default="internal_only", nullable=False)
    raw_snippet_hash: Mapped[str | None] = mapped_column(String(128))
    outcome_status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_type: Mapped[str | None] = mapped_column(String(60))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
