"""GET /providers/status and /providers/reality - provider durum raporlari."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.time import utcnow
from app.domain.models import ProviderRealityItem, ProvidersRealityResponse, ProviderStatusItem
from app.services.observation_status_service import get_observation_status_snapshot
from app.services.provider_registry import get_registry

router = APIRouter(prefix="/providers", tags=["providers"])


class ProvidersStatusResponse(BaseModel):
    providers: list[ProviderStatusItem]
    daily_job_last_run_at: str | None = None
    enabled_watchlist_count: int = 0
    enabled_url_count: int = 0
    configured_url_count: int = 0
    missing_url_count: int = 0
    attempted_url_count: int = 0
    observed_price_count: int = 0
    successful_observations: int = 0
    blocked_by_policy_count: int = 0
    blocked_by_access_count: int = 0
    blocked_count: int = 0
    parse_failed_count: int = 0
    internal_only_count: int = 0
    scrapling_enabled: bool = True
    scrapling_network_enabled: bool = True
    scrapling_available: bool = False
    scrapling_fetcher_available: bool = False
    scrapling_dynamic_fetcher_available: bool = False
    scrapling_stealthy_fetcher_available: bool = False
    scrapling_last_run_at: str | None = None
    scrapling_blocked_count: int = 0
    scrapling_parse_failed_count: int = 0
    scrapling_internal_only_count: int = 0
    scrapling_public_eligible_count: int = 0
    scrapling_warning: str | None = None
    last_attempted_urls: list[str] = Field(default_factory=list)
    last_successful_observations: list[str] = Field(default_factory=list)
    last_report_path: str | None = None
    last_issue_url: str | None = None


@router.get("/status", response_model=ProvidersStatusResponse)
def providers_status() -> ProvidersStatusResponse:
    """Tum provider'larin guncel durumunu dondurur."""
    registry = get_registry()
    snapshot = get_observation_status_snapshot()
    return ProvidersStatusResponse(
        providers=registry.all_statuses(),
        daily_job_last_run_at=snapshot.daily_job_last_run_at,
        enabled_watchlist_count=snapshot.enabled_watchlist_count,
        enabled_url_count=snapshot.enabled_url_count,
        configured_url_count=snapshot.configured_url_count,
        missing_url_count=snapshot.missing_url_count,
        attempted_url_count=snapshot.attempted_url_count,
        observed_price_count=snapshot.observed_price_count,
        successful_observations=snapshot.successful_observations,
        blocked_by_policy_count=snapshot.blocked_by_policy_count,
        blocked_by_access_count=snapshot.blocked_by_access_count,
        blocked_count=snapshot.blocked_count,
        parse_failed_count=snapshot.parse_failed_count,
        internal_only_count=snapshot.internal_only_count,
        scrapling_enabled=snapshot.scrapling_enabled,
        scrapling_network_enabled=snapshot.scrapling_network_enabled,
        scrapling_available=snapshot.scrapling_available,
        scrapling_fetcher_available=snapshot.scrapling_fetcher_available,
        scrapling_dynamic_fetcher_available=snapshot.scrapling_dynamic_fetcher_available,
        scrapling_stealthy_fetcher_available=snapshot.scrapling_stealthy_fetcher_available,
        scrapling_last_run_at=snapshot.scrapling_last_run_at,
        scrapling_blocked_count=snapshot.scrapling_blocked_count,
        scrapling_parse_failed_count=snapshot.scrapling_parse_failed_count,
        scrapling_internal_only_count=snapshot.scrapling_internal_only_count,
        scrapling_public_eligible_count=snapshot.scrapling_public_eligible_count,
        scrapling_warning=snapshot.scrapling_warning,
        last_attempted_urls=snapshot.last_attempted_urls,
        last_successful_observations=snapshot.last_successful_observations,
        last_report_path=snapshot.last_report_path,
        last_issue_url=snapshot.last_issue_url,
    )


@router.get("/reality", response_model=ProvidersRealityResponse)
def providers_reality() -> ProvidersRealityResponse:
    """Provider fiyat/stok yeteneklerini durust capability raporu olarak dondurur."""
    registry = get_registry()
    status_by_name = {item.name: item for item in registry.all_statuses()}
    implemented_names = [
        "manual_import",
        "web_observation",
        "scrapling_observation",
        "open_food_facts",
        "open_prices",
        "tesco",
        "asda",
        "sainsburys",
        "aldi",
        "lidl",
        "morrisons",
        "waitrose",
        "coop",
        "mock",
    ]
    implemented = [
        _reality_from_status(status_by_name[name])
        for name in implemented_names
        if name in status_by_name
    ]
    not_implemented = [
        ProviderRealityItem(
            name=name,
            implementation_status="not_implemented",
            can_provide_price="no",
            can_provide_stock="no",
            data_freshness="none",
            confidence="none",
            legal_safety_constraints="No public safe provider has been implemented.",
            requires_login_or_session=False,
            blocked_reason="No safe public provider is currently wired.",
            next_safe_step="Use manual_import or add a documented official/open provider.",
        )
        for name in ["iceland", "ocado", "marks_and_spencer", "farmfoods"]
    ]
    return ProvidersRealityResponse(
        generated_at=utcnow(),
        priority_order=["manual_import", "web_observation", "open_prices", "tesco", "mock"],
        providers=implemented + not_implemented,
    )


def _reality_from_status(status: ProviderStatusItem) -> ProviderRealityItem:
    if status.name == "manual_import":
        return ProviderRealityItem(
            name=status.name,
            implementation_status=status.status,
            can_provide_price="yes",
            can_provide_stock="no",
            data_freshness="manual last_checked_at or import time",
            confidence="medium",
            legal_safety_constraints="Manual data only; not live retailer stock.",
            blocked_reason=None,
            next_safe_step="Keep CSV updated with source_url and last_checked_at.",
        )
    if status.name == "open_food_facts":
        return ProviderRealityItem(
            name=status.name,
            implementation_status=status.status,
            can_provide_price="no",
            can_provide_stock="no",
            data_freshness="crowdsourced metadata",
            confidence="medium",
            legal_safety_constraints="Use custom User-Agent and respect API rate limits.",
            blocked_reason="Open Food Facts provides metadata, not supermarket prices.",
            next_safe_step="Use metadata/barcodes to support OpenPrices matching.",
        )
    if status.name == "open_prices":
        return ProviderRealityItem(
            name=status.name,
            implementation_status=status.status,
            can_provide_price="partial",
            can_provide_stock="no",
            data_freshness="open crowdsourced / historical",
            confidence="low-medium",
            legal_safety_constraints="Crowdsourced data; not official retailer price.",
            blocked_reason=None if status.status == "ok" else status.message,
            next_safe_step="Tighten barcode, currency and store mapping before using broadly.",
        )
    if status.name == "web_observation":
        return ProviderRealityItem(
            name=status.name,
            implementation_status=status.status,
            can_provide_price="partial",
            can_provide_stock="no",
            data_freshness="daily observed web page",
            confidence="low-medium",
            legal_safety_constraints="Tracked URLs only. No login/captcha/WAF bypass.",
            blocked_reason=None if status.status == "ok" else status.message,
            next_safe_step="Enable only policy-verified URLs with public_display_allowed=true.",
        )
    if status.name == "scrapling_observation":
        return ProviderRealityItem(
            name=status.name,
            implementation_status=status.status,
            can_provide_price="partial",
            can_provide_stock="no",
            data_freshness="daily observed web page (safe mode)",
            confidence="low-medium",
            legal_safety_constraints="Safe mode only. No login/captcha/proxy/stealth bypass.",
            blocked_reason=None if status.status == "ok" else status.message,
            next_safe_step="Use fixture-driven parser hardening and policy-approved exact URLs only.",
        )
    if status.name == "tesco":
        return ProviderRealityItem(
            name=status.name,
            implementation_status="limited",
            can_provide_price="partial",
            can_provide_stock="no",
            data_freshness="limited safe HTTP probe",
            confidence="low",
            legal_safety_constraints="No captcha/login/bot-protection bypass.",
            blocked_reason="Dynamic pages and bot protection make extraction unreliable.",
            next_safe_step="Use official/public API if Tesco exposes one.",
        )
    if status.name == "mock":
        return ProviderRealityItem(
            name=status.name,
            implementation_status=status.status,
            can_provide_price="yes_demo",
            can_provide_stock="no",
            data_freshness="static demo",
            confidence="demo",
            legal_safety_constraints="Must be labelled Offline demo prices.",
            blocked_reason=None,
            next_safe_step="Use only as fallback when real/manual/open providers miss.",
        )
    return ProviderRealityItem(
        name=status.name,
        implementation_status=status.status,
        can_provide_price="no",
        can_provide_stock="no",
        data_freshness="none",
        confidence="low",
        legal_safety_constraints="No captcha/login/bot-protection bypass.",
        blocked_reason=status.message or "Provider is limited.",
        next_safe_step="Use manual_import until an official/open source is documented.",
    )
