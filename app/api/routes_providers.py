"""GET /providers/status — provider durum raporu."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.domain.models import ProviderStatusItem
from app.services.provider_registry import get_registry

router = APIRouter(prefix="/providers", tags=["providers"])


class ProvidersStatusResponse(BaseModel):
    providers: list[ProviderStatusItem]


@router.get("/status", response_model=ProvidersStatusResponse)
def providers_status() -> ProvidersStatusResponse:
    """Tüm provider'ların güncel durumunu döndürür."""
    registry = get_registry()
    return ProvidersStatusResponse(providers=registry.all_statuses())
