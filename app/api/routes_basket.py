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
    return _service.compare(request)
