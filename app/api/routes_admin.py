"""POST /admin/refresh, GET /admin/runs — yönetim endpoint'leri."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.time import utcnow
from app.services.refresh_service import RefreshService

router = APIRouter(prefix="/admin", tags=["admin"])

_refresh_service = RefreshService()

# Basit in-memory run log (MVP — ilerleyen aşamada DB'ye taşınacak)
_run_log: list[dict] = []


class RefreshRequest(BaseModel):
    provider: str | None = None
    product_names: list[str] | None = None


class RefreshResponse(BaseModel):
    triggered_at: str
    results: list[dict]


class RunsResponse(BaseModel):
    runs: list[dict]


@router.post("/refresh", response_model=RefreshResponse)
def trigger_refresh(body: RefreshRequest | None = None) -> RefreshResponse:
    """
    Provider refresh'i tetikler (yerel/geliştirme kullanımı içindir).

    Üretim ortamında admin token ile korunmalıdır (.env.example'a bakın).
    """
    now = utcnow()
    req = body or RefreshRequest()

    if req.provider:
        results = [
            _refresh_service.refresh_provider(req.provider, product_names=req.product_names)
        ]
    else:
        results = _refresh_service.refresh_all(product_names=req.product_names)

    entry = {
        "triggered_at": now.isoformat(),
        "provider": req.provider or "all",
        "results": results,
    }
    _run_log.append(entry)

    return RefreshResponse(
        triggered_at=now.isoformat(),
        results=results,
    )


@router.get("/runs", response_model=RunsResponse)
def list_runs() -> RunsResponse:
    """Son provider run loglarını listeler."""
    return RunsResponse(runs=list(reversed(_run_log[-50:])))
