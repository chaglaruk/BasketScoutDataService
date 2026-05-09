"""Cache politikası — TTL kontrolü ve tazelik değerlendirmesi."""

from __future__ import annotations

from datetime import datetime

from app.core.config import get_settings
from app.core.time import is_stale
from app.domain.models import PriceItem


def is_price_stale(last_checked_at: datetime) -> bool:
    settings = get_settings()
    return is_stale(last_checked_at, settings.price_ttl_seconds)


def is_availability_stale(last_checked_at: datetime) -> bool:
    settings = get_settings()
    return is_stale(last_checked_at, settings.availability_ttl_seconds)


def annotate_staleness(items: list[PriceItem]) -> tuple[list[PriceItem], bool]:
    """
    PriceItem listesindeki eski kayıtları işaretler.

    Dönüş: (annotated_items, any_stale)
    """
    any_stale = False
    annotated: list[PriceItem] = []
    for item in items:
        stale = is_price_stale(item.last_checked_at)
        if stale:
            any_stale = True
        annotated.append(item.model_copy(update={"is_stale": stale}))
    return annotated, any_stale


def determine_data_mode(items: list[PriceItem]) -> str:
    """
    Veri modunu belirler: mock | live | cache | mixed

    - Tüm kaynaklar mock → mock
    - Tüm kaynaklar live, taze → live
    - Hiçbiri taze değil → cache
    - Karışık → mixed
    """
    if not items:
        return "mock"

    sources = {i.source for i in items}
    stale_flags = {i.is_stale for i in items}

    if sources == {"mock"}:
        return "mock"

    if True in stale_flags and False in stale_flags:
        return "mixed"

    if all(i.is_stale for i in items):
        return "cache"

    return "live"
