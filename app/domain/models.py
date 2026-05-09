"""Domain model'leri — Pydantic v2 şemaları (API + iş mantığı)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ── Temel tipler ──────────────────────────────────────────────────────────────


class ProductSummary(BaseModel):
    id: int
    canonical_name: str
    category: str | None = None
    brand: str | None = None
    aliases: list[str] = Field(default_factory=list)
    source: str
    confidence: float = 1.0


class PriceItem(BaseModel):
    retailer: str
    retailer_slug: str
    product: str
    price: float
    currency: str = "GBP"
    unit_price: float | None = None
    unit_price_unit: str | None = None
    loyalty_price: float | None = None
    own_brand: bool = False
    available: bool | None = None
    raw_availability_text: str | None = None
    source: str
    source_url: str | None = None
    last_checked_at: datetime
    confidence: float
    is_stale: bool = False


# ── Basket compare ────────────────────────────────────────────────────────────


class BasketItem(BaseModel):
    name: str
    quantity: int = 1


class BasketCompareRequest(BaseModel):
    postcode: str | None = None
    coverage_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    use_loyalty_prices: bool = False
    allow_own_brand: bool = True
    items: list[BasketItem]


class BasketLineItem(BaseModel):
    requested_name: str
    canonical_name: str | None = None
    quantity: int
    unit_price: float | None = None
    line_total: float | None = None
    available: bool | None = None
    source: str | None = None
    source_url: str | None = None
    last_checked_at: datetime | None = None
    confidence: float | None = None
    is_stale: bool = False


class StoreBasketResult(BaseModel):
    retailer: str
    retailer_slug: str
    qualifies: bool
    total_price: float
    coverage: float
    matched_count: int
    missing_items: list[str] = Field(default_factory=list)
    line_items: list[BasketLineItem] = Field(default_factory=list)


class BasketCompareRecommended(BaseModel):
    retailer: str
    total_price: float
    coverage: float
    matched_count: int
    requested_count: int
    missing_items: list[str] = Field(default_factory=list)
    savings_vs_priciest: float = 0.0


class BasketCompareMetadata(BaseModel):
    data_mode: str  # mock | live | cache | mixed
    generated_at: datetime
    warnings: list[str] = Field(default_factory=list)


class BasketCompareResponse(BaseModel):
    recommended: BasketCompareRecommended | None = None
    stores: list[StoreBasketResult] = Field(default_factory=list)
    metadata: BasketCompareMetadata


# ── Provider ──────────────────────────────────────────────────────────────────


class ProviderStatusItem(BaseModel):
    name: str = Field(description="Provider id (ör. tesco)")
    status: str = Field(description="Durum: ok, limited, blocked")
    type: str = Field(description="Tip: mock, manual, open_data, scraping")
    last_run_at: datetime | None = Field(None, description="Son çalışma/probe zamanı")
    message: str | None = Field(None, description="Hata veya durum mesajı")
    limitations: list[str] = Field(default_factory=list, description="Kısıtlamalar listesi")
    supports_live_prices: bool = Field(default=False, description="Canlı fiyat sorgulamayı destekler mi")
    supports_stock: bool = Field(default=False, description="Canlı stok sorgulamayı destekler mi")
    confidence_score: float | None = Field(default=None, description="Fiyatların güvenilirlik skoru")
    requires_postcode: bool = False
