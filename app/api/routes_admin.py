"""POST /admin/refresh, GET /admin/runs — yönetim endpoint'leri."""

from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.core.time import utcnow
from app.domain.models import ManualImportSummary, ManualPriceImportItem
from app.services.manual_import_service import ManualImportService
from app.services.provider_registry import get_registry
from app.services.refresh_service import RefreshService

router = APIRouter(prefix="/admin", tags=["admin"])

_refresh_service = RefreshService()
_manual_service = ManualImportService()

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


class ProviderPriorityResponse(BaseModel):
    priority_order: list[str]
    description: str


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


@router.get("/manual-prices", response_model=list[ManualPriceImportItem])
def list_manual_prices() -> list[ManualPriceImportItem]:
    """Tüm manuel fiyat kayıtlarını listeler."""
    return _manual_service.get_all()


@router.post("/manual-prices/import", response_model=ManualImportSummary)
def import_manual_prices(items: list[ManualPriceImportItem]) -> ManualImportSummary:
    """Yeni manuel fiyat kayıtlarını içe aktarır."""
    summary = _manual_service.import_items(items)

    # Provider'ı yenile
    registry = get_registry()
    manual_provider = registry.get("manual_import")
    if manual_provider and hasattr(manual_provider, "reload"):
        manual_provider.reload()

    return summary


@router.get("/manual-prices/template")
def get_manual_prices_template():
    """CSV şablonu döndürür."""
    content = _manual_service.get_template_csv()
    return Response(content=content, media_type="text/csv")


@router.get("/provider-priority", response_model=ProviderPriorityResponse)
def get_provider_priority() -> ProviderPriorityResponse:
    """Aktif provider öncelik sırasını gösterir."""
    # ProviderRegistry._select_providers içindeki sırayla aynı olmalı
    order = ["manual_import", "open_prices", "tesco", "mock"]
    return ProviderPriorityResponse(
        priority_order=order,
        description="Fiyat karşılaştırmasında kullanılan öncelik sırası (yukarıdan aşağıya)."
    )
