"""GET /prices/latest — güncel fiyat sorgulama endpoint'i."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.errors import bad_request
from app.domain.models import PriceItem
from app.services.price_service import PriceService

router = APIRouter(prefix="/prices", tags=["prices"])

_service = PriceService()


class PricesResponse(BaseModel):
    query: str
    postcode: str | None = None
    items: list[PriceItem]
    count: int
    any_stale: bool = False
    warning: str | None = None


@router.get("/latest", response_model=PricesResponse)
def get_latest_prices(
    product: str = Query(..., min_length=1, max_length=200, description="Ürün adı"),
    postcode: str | None = Query(
        None, max_length=10, description="İngiltere posta kodu (opsiyonel)"
    ),
    provider: str | None = Query(None, description="Provider adı (opsiyonel)"),
) -> PricesResponse:
    """Verilen ürün için bilinen en güncel fiyatları döndürür."""
    if not product.strip():
        raise bad_request("Ürün adı boş olamaz.")

    provider_names = [provider] if provider else None
    items, any_stale = _service.get_latest(
        [product.strip()],
        postcode=postcode,
        provider_names=provider_names,
    )

    warning = None
    if any_stale:
        warning = "Bazı fiyat verileri güncel değil (TTL aşıldı)."

    return PricesResponse(
        query=product,
        postcode=postcode,
        items=items,
        count=len(items),
        any_stale=any_stale,
        warning=warning,
    )
