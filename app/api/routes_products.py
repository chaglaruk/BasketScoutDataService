"""GET /products/search — ürün arama endpoint'i."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.errors import bad_request
from app.domain.models import ProductSummary
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

_service = ProductService()


class ProductSearchResponse(BaseModel):
    query: str
    items: list[ProductSummary]
    count: int


@router.get("/search", response_model=ProductSearchResponse)
def search_products(
    q: str = Query(..., min_length=1, max_length=200, description="Arama terimi"),
    provider: str | None = Query(None, description="Belirli bir provider adı (opsiyonel)"),
) -> ProductSearchResponse:
    """Ürün adı veya alias ile arama yapar."""
    if not q.strip():
        raise bad_request("Arama terimi boş olamaz.")

    provider_names = [provider] if provider else None
    items = _service.search(q.strip(), provider_names=provider_names)

    return ProductSearchResponse(
        query=q,
        items=items,
        count=len(items),
    )
