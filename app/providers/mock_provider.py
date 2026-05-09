"""MockProvider — deterministik demo verisi, test ve geliştirme için."""

from __future__ import annotations

from app.core.time import utcnow
from app.domain.models import PriceItem, ProductSummary, ProviderStatusItem
from app.domain.normalization import normalize_name
from app.providers.base import BaseProvider

# ── Demo veri ─────────────────────────────────────────────────────────────────

_RETAILERS = [
    {"name": "Tesco", "slug": "tesco"},
    {"name": "Asda", "slug": "asda"},
    {"name": "Sainsbury's", "slug": "sainsburys"},
    {"name": "Morrisons", "slug": "morrisons"},
    {"name": "Waitrose", "slug": "waitrose"},
    {"name": "Co-op", "slug": "coop"},
    {"name": "Aldi", "slug": "aldi"},
    {"name": "Lidl", "slug": "lidl"},
]

_PRODUCTS = [
    {
        "id": 1,
        "canonical_name": "Semi-Skimmed Milk 2L",
        "category": "Dairy",
        "brand": None,
        "aliases": ["milk", "semi skimmed milk", "2l milk", "full fat milk"],
    },
    {
        "id": 2,
        "canonical_name": "White Bread 800g",
        "category": "Bakery",
        "brand": "Hovis",
        "aliases": ["bread", "white bread", "sliced bread", "loaf"],
    },
    {
        "id": 3,
        "canonical_name": "Free Range Eggs 6 Pack",
        "category": "Dairy & Eggs",
        "brand": None,
        "aliases": ["eggs", "6 eggs", "free range eggs", "egg"],
    },
    {
        "id": 4,
        "canonical_name": "Cheddar Cheese 400g",
        "category": "Dairy",
        "brand": "Cathedral City",
        "aliases": ["cheese", "cheddar", "cheddar cheese"],
    },
    {
        "id": 5,
        "canonical_name": "Unsalted Butter 250g",
        "category": "Dairy",
        "brand": "Anchor",
        "aliases": ["butter", "unsalted butter"],
    },
    {
        "id": 6,
        "canonical_name": "Chicken Breast Fillets 500g",
        "category": "Meat",
        "brand": None,
        "aliases": ["chicken", "chicken breast", "chicken fillets"],
    },
    {
        "id": 7,
        "canonical_name": "Spaghetti 500g",
        "category": "Pasta & Rice",
        "brand": "Barilla",
        "aliases": ["pasta", "spaghetti", "dried pasta"],
    },
    {
        "id": 8,
        "canonical_name": "Chopped Tomatoes 400g",
        "category": "Tinned",
        "brand": "Napolina",
        "aliases": ["chopped tomatoes", "tinned tomatoes", "canned tomatoes", "tomatoes"],
    },
    {
        "id": 9,
        "canonical_name": "Orange Juice 1L",
        "category": "Juice & Drinks",
        "brand": "Tropicana",
        "aliases": ["orange juice", "OJ", "juice"],
    },
    {
        "id": 10,
        "canonical_name": "Bananas per kg",
        "category": "Fruit",
        "brand": None,
        "aliases": ["bananas", "banana"],
    },
]

# Fiyat matrisi: (product_id, retailer_slug) -> (price, loyalty_price, available, own_brand)
_PRICES: dict[tuple[int, str], tuple[float, float | None, bool, bool]] = {
    (1, "tesco"): (1.55, 1.40, True, False),
    (1, "asda"): (1.50, None, True, False),
    (1, "sainsburys"): (1.65, 1.50, True, False),
    (1, "morrisons"): (1.60, 1.45, True, False),
    (1, "waitrose"): (1.85, None, True, False),
    (1, "coop"): (1.70, None, True, False),
    (1, "aldi"): (1.29, None, True, True),
    (1, "lidl"): (1.35, None, True, True),
    (2, "tesco"): (1.10, None, True, False),
    (2, "asda"): (1.05, None, True, False),
    (2, "sainsburys"): (1.15, None, True, False),
    (2, "morrisons"): (1.10, None, True, False),
    (2, "waitrose"): (1.40, None, True, False),
    (2, "coop"): (1.20, None, True, False),
    (2, "aldi"): (0.89, None, True, True),
    (2, "lidl"): (0.89, None, True, True),
    (3, "tesco"): (2.25, 2.00, True, False),
    (3, "asda"): (2.10, None, True, False),
    (3, "sainsburys"): (2.30, 2.10, True, False),
    (3, "morrisons"): (2.20, None, True, False),
    (3, "waitrose"): (2.75, None, True, False),
    (3, "coop"): (2.40, None, True, False),
    (3, "aldi"): (1.79, None, True, True),
    (3, "lidl"): (1.85, None, True, True),
    (4, "tesco"): (3.50, 3.00, True, False),
    (4, "asda"): (3.25, None, True, False),
    (4, "sainsburys"): (3.75, 3.25, True, False),
    (4, "morrisons"): (3.50, None, True, False),
    (4, "waitrose"): (4.50, None, True, False),
    (4, "coop"): (3.90, None, False, False),
    (4, "aldi"): (2.49, None, True, True),
    (4, "lidl"): (2.59, None, True, True),
    (5, "tesco"): (1.75, None, True, False),
    (5, "asda"): (1.70, None, True, False),
    (5, "sainsburys"): (1.80, None, True, False),
    (5, "morrisons"): (1.75, None, True, False),
    (5, "waitrose"): (2.20, None, True, False),
    (5, "coop"): (1.90, None, True, False),
    (5, "aldi"): (1.45, None, True, True),
    (5, "lidl"): (1.49, None, True, True),
    (6, "tesco"): (4.50, 4.00, True, False),
    (6, "asda"): (4.25, None, True, False),
    (6, "sainsburys"): (4.75, 4.25, True, False),
    (6, "morrisons"): (4.50, None, True, False),
    (6, "waitrose"): (5.50, None, True, False),
    (6, "coop"): (4.80, None, True, False),
    (6, "aldi"): (3.49, None, True, True),
    (6, "lidl"): (3.59, None, True, True),
    (7, "tesco"): (1.50, None, True, False),
    (7, "asda"): (1.45, None, True, False),
    (7, "sainsburys"): (1.55, None, True, False),
    (7, "morrisons"): (1.50, None, True, False),
    (7, "waitrose"): (1.90, None, True, False),
    (7, "coop"): (1.60, None, True, False),
    (7, "aldi"): (0.99, None, True, True),
    (7, "lidl"): (0.99, None, True, True),
    (8, "tesco"): (0.75, None, True, False),
    (8, "asda"): (0.70, None, True, False),
    (8, "sainsburys"): (0.80, None, True, False),
    (8, "morrisons"): (0.75, None, True, False),
    (8, "waitrose"): (0.95, None, True, False),
    (8, "coop"): (0.85, None, True, False),
    (8, "aldi"): (0.55, None, True, True),
    (8, "lidl"): (0.55, None, True, True),
    (9, "tesco"): (2.00, None, True, False),
    (9, "asda"): (1.90, None, True, False),
    (9, "sainsburys"): (2.10, None, True, False),
    (9, "morrisons"): (2.00, None, True, False),
    (9, "waitrose"): (2.50, None, True, False),
    (9, "coop"): (2.20, None, True, False),
    (9, "aldi"): (1.49, None, True, True),
    (9, "lidl"): (1.55, None, True, True),
    (10, "tesco"): (0.99, None, True, False),
    (10, "asda"): (0.95, None, True, False),
    (10, "sainsburys"): (1.05, None, True, False),
    (10, "morrisons"): (0.99, None, True, False),
    (10, "waitrose"): (1.25, None, True, False),
    (10, "coop"): (1.10, None, True, False),
    (10, "aldi"): (0.75, None, True, True),
    (10, "lidl"): (0.75, None, True, True),
}


class MockProvider(BaseProvider):
    """
    Gerçekçi İngiltere süpermarket demo verisi sunan mock provider.
    Varsayılan provider. Her zaman çalışır, deterministiktir.
    """

    @property
    def name(self) -> str:
        return "mock"

    @property
    def type(self) -> str:
        return "mock"

    @property
    def supports_live_prices(self) -> bool:
        return False  # Demo verisi, canlı değil

    @property
    def supports_stock(self) -> bool:
        return True  # Demo stok verisi var

    @property
    def limitations(self) -> list[str]:
        return [
            "Demo verisi — gerçek fiyatları yansıtmaz.",
            "Fiyatlar gerçek zamanlı değil, statik referans değerleridir.",
            "Canlı promosyonlar dahil değil.",
        ]

    def status(self) -> ProviderStatusItem:
        return ProviderStatusItem(
            name=self.name,
            status="ok",
            type=self.type,
            last_run_at=utcnow(),
            message="Mock provider aktif — demo veri sunuluyor.",
            limitations=self.limitations,
            supports_live_prices=self.supports_live_prices,
            supports_stock=self.supports_stock,
            requires_postcode=self.requires_postcode,
        )

    def search_products(self, query: str) -> list[ProductSummary]:
        nq = normalize_name(query)
        results: list[ProductSummary] = []
        for p in _PRODUCTS:
            # Canonical isimde ara
            if nq in normalize_name(p["canonical_name"]):
                results.append(self._to_summary(p))
                continue
            # Alias'larda ara
            for alias in p.get("aliases", []):
                if nq in normalize_name(alias) or normalize_name(alias) in nq:
                    results.append(self._to_summary(p))
                    break
        return results

    def get_latest_prices(
        self,
        product_names: list[str],
        postcode: str | None = None,
    ) -> list[PriceItem]:
        items: list[PriceItem] = []
        checked_at = utcnow()

        for name in product_names:
            nname = normalize_name(name)
            matched_products = [
                p
                for p in _PRODUCTS
                if nname in normalize_name(p["canonical_name"])
                or any(
                    nname in normalize_name(a) or normalize_name(a) in nname
                    for a in p.get("aliases", [])
                )
            ]
            for product in matched_products:
                for retailer in _RETAILERS:
                    key = (product["id"], retailer["slug"])
                    if key not in _PRICES:
                        continue
                    price, loyalty, available, own_brand = _PRICES[key]
                    items.append(
                        PriceItem(
                            retailer=retailer["name"],
                            retailer_slug=retailer["slug"],
                            product=product["canonical_name"],
                            price=price,
                            currency="GBP",
                            loyalty_price=loyalty,
                            own_brand=own_brand,
                            available=available,
                            source="mock",
                            last_checked_at=checked_at,
                            confidence=1.0,
                            is_stale=False,
                        )
                    )
        return items

    def refresh_products(
        self,
        product_names: list[str] | None = None,
        postcode: str | None = None,
    ) -> dict:
        return {
            "provider": self.name,
            "status": "ok",
            "products_checked": len(_PRODUCTS),
            "message": "Mock veri zaten güncel.",
        }

    def _to_summary(self, p: dict) -> ProductSummary:
        return ProductSummary(
            id=p["id"],
            canonical_name=p["canonical_name"],
            category=p.get("category"),
            brand=p.get("brand"),
            aliases=p.get("aliases", []),
            source="mock",
            confidence=1.0,
        )

    def get_retailers(self) -> list[dict]:
        return list(_RETAILERS)

    def get_all_products(self) -> list[dict]:
        return list(_PRODUCTS)
