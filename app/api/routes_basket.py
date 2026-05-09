"""POST /basket/compare — sepet karşılaştırma endpoint'i."""

from __future__ import annotations

from fastapi import APIRouter

from app.domain.models import BasketCompareRequest, BasketCompareResponse
from app.services.basket_service import BasketService

router = APIRouter(prefix="/basket", tags=["basket"])

_service = BasketService()


@router.post("/compare", response_model=BasketCompareResponse)
def compare_basket(request: BasketCompareRequest) -> BasketCompareResponse:
    """
    Verilen sepeti tüm aktif perakendecilerde karşılaştırır.

    En ucuz ve kapsamayı karşılayan mağazayı önerir.
    Her satır için veri kaynağı, güven ve tazelik bilgisi döndürülür.
    """
    response = _service.compare(request)
    
    # Metadata transparency
    from app.services.provider_registry import get_registry
    from app.core.time import utcnow
    
    registry = get_registry()
    status_summary = {p.name: p.status().status for p in registry.all()}
    
    stale_or_low_confidence_count = 0
    for store in response.stores:
        for item in store.line_items:
            if item.is_stale or (item.confidence is not None and item.confidence < 0.8):
                stale_or_low_confidence_count += 1
                
    response.metadata.provider_status_summary = status_summary
    response.metadata.stale_or_low_confidence_count = stale_or_low_confidence_count
    
    return response
