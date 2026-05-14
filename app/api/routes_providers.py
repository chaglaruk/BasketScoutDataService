"""GET /providers/status and /providers/reality - provider durum raporlari."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.time import utcnow
from app.domain.models import ProviderRealityItem, ProvidersRealityResponse, ProviderStatusItem
from app.services.provider_registry import get_registry

router = APIRouter(prefix="/providers", tags=["providers"])


class ProvidersStatusResponse(BaseModel):
    providers: list[ProviderStatusItem]


@router.get("/status", response_model=ProvidersStatusResponse)
def providers_status() -> ProvidersStatusResponse:
    """Tum provider'larin guncel durumunu dondurur."""
    registry = get_registry()
    return ProvidersStatusResponse(providers=registry.all_statuses())


@router.get("/reality", response_model=ProvidersRealityResponse)
def providers_reality() -> ProvidersRealityResponse:
    """Provider fiyat/stok yeteneklerini durust capability raporu olarak dondurur."""
    registry = get_registry()
    status_by_name = {item.name: item for item in registry.all_statuses()}
    implemented_names = [
        "manual_import",
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
        priority_order=["manual_import", "open_prices", "tesco", "mock"],
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
