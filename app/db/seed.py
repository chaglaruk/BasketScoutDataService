"""Veritabanı seed — demo retailer ve ürün verisi ekler."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_engine
from app.db.models import Product, ProductAlias, Retailer, WebPriceWatchlist

logger = logging.getLogger(__name__)

_RETAILERS = [
    ("Tesco", "tesco", "https://www.tesco.com", "ok"),
    ("Asda", "asda", "https://www.asda.com", "ok"),
    ("Sainsbury's", "sainsburys", "https://www.sainsburys.co.uk", "limited"),
    ("Morrisons", "morrisons", "https://groceries.morrisons.com", "limited"),
    ("Waitrose", "waitrose", "https://www.waitrose.com", "limited"),
    ("Co-op", "coop", "https://shop.coop.co.uk", "limited"),
    ("Aldi", "aldi", "https://www.aldi.co.uk", "limited"),
    ("Lidl", "lidl", "https://www.lidl.co.uk", "limited"),
]

_PRODUCTS = [
    (1, "Semi-Skimmed Milk 2L", "dairy", None, ["milk", "semi skimmed milk", "2l milk"]),
    (2, "White Bread 800g", "bakery", "Hovis", ["bread", "white bread", "sliced bread"]),
    (3, "Free Range Eggs 6 Pack", "dairy & eggs", None, ["eggs", "6 eggs", "free range eggs"]),
    (4, "Cheddar Cheese 400g", "dairy", "Cathedral City", ["cheese", "cheddar"]),
    (5, "Unsalted Butter 250g", "dairy", "Anchor", ["butter", "unsalted butter"]),
    (6, "Chicken Breast Fillets 500g", "meat", None, ["chicken", "chicken breast"]),
    (7, "Spaghetti 500g", "pasta & rice", "Barilla", ["pasta", "spaghetti"]),
    (8, "Chopped Tomatoes 400g", "tinned", "Napolina", ["chopped tomatoes", "tinned tomatoes"]),
    (9, "Orange Juice 1L", "juice & drinks", "Tropicana", ["orange juice", "juice"]),
    (10, "Bananas per kg", "fruit", None, ["bananas", "banana"]),
]

_WATCHLIST_BASE = [
    ("tesco", "Tesco"),
    ("aldi", "Aldi"),
    ("sainsburys", "Sainsbury's"),
    ("lidl", "Lidl"),
]
_WATCHLIST_PRODUCTS = [
    "Semi-Skimmed Milk 2L",
    "White Bread 800g",
]


def seed_all() -> None:
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    db = SessionLocal()
    try:
        _seed_retailers(db)
        _seed_products(db)
        _seed_web_watchlist(db)
        db.commit()
        logger.info("Seed tamamlandı.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Seed hatası: {exc}")
        raise
    finally:
        db.close()


def _seed_retailers(db: Session) -> None:
    from sqlalchemy import select

    for name, slug, url, status in _RETAILERS:
        existing = db.scalar(select(Retailer).where(Retailer.slug == slug))
        if existing is None:
            db.add(
                Retailer(
                    name=name,
                    slug=slug,
                    website_url=url,
                    country="GB",
                    enabled=True,
                    provider_status=status,
                )
            )
    db.flush()


def _seed_products(db: Session) -> None:
    from sqlalchemy import select

    from app.domain.normalization import normalize_name

    for _pid, canonical, category, brand, aliases in _PRODUCTS:
        existing = db.scalar(
            select(Product).where(Product.normalized_name == normalize_name(canonical))
        )
        if existing is None:
            p = Product(
                canonical_name=canonical,
                normalized_name=normalize_name(canonical),
                category=category,
                brand=brand,
            )
            db.add(p)
            db.flush()
            for alias in aliases:
                db.add(
                    ProductAlias(
                        product_id=p.id,
                        alias=alias,
                        normalized_alias=normalize_name(alias),
                        source="seed",
                    )
                )
    db.flush()


def _seed_web_watchlist(db: Session) -> None:
    from sqlalchemy import select

    for retailer_slug, retailer_name in _WATCHLIST_BASE:
        for canonical_name in _WATCHLIST_PRODUCTS:
            existing = db.scalar(
                select(WebPriceWatchlist).where(
                    WebPriceWatchlist.retailer_slug == retailer_slug,
                    WebPriceWatchlist.canonical_product_name == canonical_name,
                )
            )
            if existing is not None:
                continue
            db.add(
                WebPriceWatchlist(
                    retailer_slug=retailer_slug,
                    retailer_name=retailer_name,
                    canonical_product_name=canonical_name,
                    product_url=None,
                    expected_product_keywords=None,
                    enabled=False,
                    max_frequency_hours=24,
                    policy_status="unconfigured",
                    public_display_allowed=False,
                    notes="No exact safe public product URL documented yet.",
                )
            )
    db.flush()
