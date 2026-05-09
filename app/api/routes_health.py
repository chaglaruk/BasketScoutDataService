"""GET /health — servis sağlık kontrolü."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.time import utcnow

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    time: datetime
    env: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Servis sağlık durumunu döndürür."""
    s = get_settings()
    return HealthResponse(
        ok=True,
        service="BasketScoutDataService",
        version=s.app_version,
        time=utcnow(),
        env=s.app_env,
    )
