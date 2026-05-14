"""POST /admin/refresh, GET /admin/runs — yönetim endpoint'leri."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.time import utcnow
from app.domain.models import ManualCsvValidationReport, ManualImportSummary, ManualPriceImportItem
from app.services.manual_import_service import ManualImportService
from app.services.provider_registry import get_registry
from app.services.refresh_service import RefreshService

header_scheme = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def check_admin_auth(token: str = Depends(header_scheme)):
    settings = get_settings()
    if (
        settings.is_production
        and settings.require_admin_token_in_production
        and not settings.admin_token
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ADMIN_TOKEN is required in production for /admin endpoints. "
                "Set ADMIN_TOKEN before public deployment."
            ),
        )
    # Eğer admin_token ayarlanmışsa kontrol et
    if settings.admin_token and (not token or token != settings.admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik admin token (X-Admin-Token header gerekli)."
        )
    return True


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(check_admin_auth)]
)

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


@router.post("/manual-prices/validate-csv", response_model=ManualCsvValidationReport)
def validate_manual_prices_csv(
    csv_body: str = Body(..., media_type="text/csv"),
) -> ManualCsvValidationReport:
    """Validate a manual price CSV body without changing stored data."""
    return _manual_service.validate_csv_text(csv_body)


@router.post("/manual-prices/import-csv", response_model=ManualImportSummary)
def import_manual_prices_csv(
    csv_body: str = Body(..., media_type="text/csv"),
) -> ManualImportSummary:
    """Import manual prices from a CSV body. Invalid rows are skipped."""
    summary = _manual_service.import_csv_text(csv_body)

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


@router.get("/manual-prices/export")
def export_manual_prices():
    """Export current manual prices as CSV."""
    content = _manual_service.export_csv()
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
