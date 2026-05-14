"""Admin routes: refresh, manual import, watchlist and daily observation operations."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.time import utcnow
from app.db.database import SessionLocal, get_engine, init_db
from app.db.repositories import WebPriceWatchlistRepository
from app.domain.models import ManualCsvValidationReport, ManualImportSummary, ManualPriceImportItem
from app.services.manual_import_service import ManualImportService
from app.services.provider_registry import get_registry
from app.services.refresh_service import RefreshService
from app.services.scrapling_price_observation_service import (
    report_to_dict as scrapling_report_to_dict,
)
from app.services.scrapling_price_observation_service import (
    run_scrapling_price_observation,
)
from app.services.web_price_observation_service import report_to_dict, run_daily_price_observation

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
    if settings.admin_token and (not token or token != settings.admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token (X-Admin-Token header required).",
        )
    return True


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(check_admin_auth)],
)

_refresh_service = RefreshService()
_manual_service = ManualImportService()

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


class WebWatchlistItemResponse(BaseModel):
    id: int
    retailer_slug: str
    retailer_name: str
    canonical_product_name: str
    product_url: str | None = None
    expected_product_keywords: str | None = None
    enabled: bool
    max_frequency_hours: int
    robots_checked_at: str | None = None
    policy_status: str
    public_display_allowed: bool
    last_attempt_at: str | None = None
    last_success_at: str | None = None
    last_error: str | None = None
    notes: str | None = None


class WebWatchlistUpsertRequest(BaseModel):
    retailer_slug: str
    retailer_name: str
    canonical_product_name: str
    product_url: str | None = None
    expected_product_keywords: str | None = None
    enabled: bool = False
    max_frequency_hours: int = 24
    policy_status: str = "unconfigured"
    public_display_allowed: bool = False
    notes: str | None = None


class DailyObservationRunRequest(BaseModel):
    provider: str = "default"
    dry_run: bool = False
    force: bool = False


@router.post("/refresh", response_model=RefreshResponse)
def trigger_refresh(body: RefreshRequest | None = None) -> RefreshResponse:
    now = utcnow()
    req = body or RefreshRequest()

    if req.provider:
        results = [_refresh_service.refresh_provider(req.provider, product_names=req.product_names)]
    else:
        results = _refresh_service.refresh_all(product_names=req.product_names)

    entry = {
        "triggered_at": now.isoformat(),
        "provider": req.provider or "all",
        "results": results,
    }
    _run_log.append(entry)

    return RefreshResponse(triggered_at=now.isoformat(), results=results)


@router.get("/runs", response_model=RunsResponse)
def list_runs() -> RunsResponse:
    return RunsResponse(runs=list(reversed(_run_log[-50:])))


@router.get("/manual-prices", response_model=list[ManualPriceImportItem])
def list_manual_prices() -> list[ManualPriceImportItem]:
    return _manual_service.get_all()


@router.post("/manual-prices/import", response_model=ManualImportSummary)
def import_manual_prices(items: list[ManualPriceImportItem]) -> ManualImportSummary:
    summary = _manual_service.import_items(items)

    registry = get_registry()
    manual_provider = registry.get("manual_import")
    if manual_provider and hasattr(manual_provider, "reload"):
        manual_provider.reload()

    return summary


@router.get("/manual-prices/template")
def get_manual_prices_template():
    content = _manual_service.get_template_csv()
    return Response(content=content, media_type="text/csv")


@router.get("/manual-prices/export")
def export_manual_prices():
    content = _manual_service.export_csv()
    return Response(content=content, media_type="text/csv")


@router.post("/manual-prices/validate-csv", response_model=ManualCsvValidationReport)
def validate_manual_prices_csv(
    csv_body: str = Body(..., media_type="text/csv"),
) -> ManualCsvValidationReport:
    return _manual_service.validate_csv_text(csv_body)


@router.post("/manual-prices/import-csv", response_model=ManualImportSummary)
def import_manual_prices_csv(
    csv_body: str = Body(..., media_type="text/csv"),
) -> ManualImportSummary:
    summary = _manual_service.import_csv_text(csv_body)

    registry = get_registry()
    manual_provider = registry.get("manual_import")
    if manual_provider and hasattr(manual_provider, "reload"):
        manual_provider.reload()

    return summary


@router.get("/provider-priority", response_model=ProviderPriorityResponse)
def get_provider_priority() -> ProviderPriorityResponse:
    order = ["manual_import", "web_observation", "open_prices", "tesco", "mock"]
    return ProviderPriorityResponse(
        priority_order=order,
        description="Comparison provider order from highest priority to fallback.",
    )


@router.get("/web-watchlist", response_model=list[WebWatchlistItemResponse])
def list_web_watchlist() -> list[WebWatchlistItemResponse]:
    init_db()
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        rows = WebPriceWatchlistRepository(db).get_all()
        return [
            WebWatchlistItemResponse(
                id=row.id,
                retailer_slug=row.retailer_slug,
                retailer_name=row.retailer_name,
                canonical_product_name=row.canonical_product_name,
                product_url=row.product_url,
                expected_product_keywords=row.expected_product_keywords,
                enabled=row.enabled,
                max_frequency_hours=row.max_frequency_hours,
                robots_checked_at=row.robots_checked_at.isoformat() if row.robots_checked_at else None,
                policy_status=row.policy_status,
                public_display_allowed=row.public_display_allowed,
                last_attempt_at=row.last_attempt_at.isoformat() if row.last_attempt_at else None,
                last_success_at=row.last_success_at.isoformat() if row.last_success_at else None,
                last_error=row.last_error,
                notes=row.notes,
            )
            for row in rows
        ]
    finally:
        db.close()


@router.post("/web-watchlist/upsert", response_model=WebWatchlistItemResponse)
def upsert_web_watchlist(item: WebWatchlistUpsertRequest) -> WebWatchlistItemResponse:
    init_db()
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        row = WebPriceWatchlistRepository(db).upsert(
            retailer_slug=item.retailer_slug,
            retailer_name=item.retailer_name,
            canonical_product_name=item.canonical_product_name,
            product_url=item.product_url,
            expected_product_keywords=item.expected_product_keywords,
            enabled=item.enabled,
            max_frequency_hours=item.max_frequency_hours,
            policy_status=item.policy_status,
            public_display_allowed=item.public_display_allowed,
            notes=item.notes,
        )
        db.commit()
        return WebWatchlistItemResponse(
            id=row.id,
            retailer_slug=row.retailer_slug,
            retailer_name=row.retailer_name,
            canonical_product_name=row.canonical_product_name,
            product_url=row.product_url,
            expected_product_keywords=row.expected_product_keywords,
            enabled=row.enabled,
            max_frequency_hours=row.max_frequency_hours,
            robots_checked_at=row.robots_checked_at.isoformat() if row.robots_checked_at else None,
            policy_status=row.policy_status,
            public_display_allowed=row.public_display_allowed,
            last_attempt_at=row.last_attempt_at.isoformat() if row.last_attempt_at else None,
            last_success_at=row.last_success_at.isoformat() if row.last_success_at else None,
            last_error=row.last_error,
            notes=row.notes,
        )
    finally:
        db.close()


@router.post("/daily-observation/run")
def run_daily_observation(body: DailyObservationRunRequest) -> dict:
    if body.provider == "scrapling":
        report = run_scrapling_price_observation(dry_run=body.dry_run, force=body.force)
        return scrapling_report_to_dict(report)
    report = run_daily_price_observation(dry_run=body.dry_run, force=body.force)
    return report_to_dict(report)
