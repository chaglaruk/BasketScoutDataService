"""GET /prices/latest â€” gÃ¼ncel fiyat sorgulama endpoint'i."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.errors import bad_request
from app.domain.models import PriceItem
from app.services.price_service import PriceService
from app.services.provider_registry import get_registry

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
    product: str = Query(..., min_length=1, max_length=200, description="ÃœrÃ¼n adÄ±"),
    postcode: str | None = Query(
        None, max_length=10, description="Ä°ngiltere posta kodu (opsiyonel)"
    ),
    provider: str | None = Query(None, description="Provider adÄ± (opsiyonel)"),
) -> PricesResponse:
    """Verilen Ã¼rÃ¼n iÃ§in bilinen en gÃ¼ncel fiyatlarÄ± dÃ¶ndÃ¼rÃ¼r."""
    if not product.strip():
        raise bad_request("ÃœrÃ¼n adÄ± boÅŸ olamaz.")

    provider_names = [provider] if provider else None
    result = _service.get_latest(
        [product.strip()],
        postcode=postcode,
        provider_names=provider_names,
    )

    warning = None
    if result.any_stale:
        warning = "Bazi fiyat verileri guncel degil (TTL asildi)."
    if result.why_mock_used:
        warning = result.why_mock_used if warning is None else f"{warning} {result.why_mock_used}"
    if provider and not result.items:
        provider_obj = get_registry().get(provider)
        details = ""
        if provider_obj:
            limitations = provider_obj.limitations
            if limitations:
                details = f" {limitations[-1]}"
        provider_warning = (
            f"Provider '{provider}' returned no price data for '{product.strip()}'."
            f"{details}"
        )
        warning = provider_warning if warning is None else f"{warning} {provider_warning}"

    return PricesResponse(
        query=product,
        postcode=postcode,
        items=result.items,
        count=len(result.items),
        any_stale=result.any_stale,
        warning=warning,
    )
