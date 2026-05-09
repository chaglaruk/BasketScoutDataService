"""Güven skoru hesaplama modeli."""

from __future__ import annotations

from datetime import datetime

from app.core.config import get_settings
from app.core.time import seconds_since


def price_confidence(
    base_confidence: float,
    last_checked_at: datetime,
    source_type: str,
) -> float:
    """
    Fiyat güven skorunu hesaplar.

    - Taze live veri: temel skor
    - Eski veri: azalan skor
    - Mock veri: 1.0 (demo amaçlı)
    - Crowdsourced: 0.6 tavan
    """
    settings = get_settings()
    ttl = settings.price_ttl_seconds
    age = seconds_since(last_checked_at)

    if source_type == "mock":
        return 1.0

    if source_type == "crowdsourced":
        base_confidence = min(base_confidence, 0.6)

    if age <= ttl:
        return round(base_confidence, 4)

    # TTL aşıldıkça güven azalır (yarılanma mantığı)
    decay = max(0.1, base_confidence * (ttl / (age + ttl)))
    return round(decay, 4)


def availability_confidence(
    base_confidence: float,
    last_checked_at: datetime,
    source_type: str,
) -> float:
    """Stok güven skorunu hesaplar."""
    settings = get_settings()
    ttl = settings.availability_ttl_seconds
    age = seconds_since(last_checked_at)

    if source_type == "mock":
        return 1.0

    if age <= ttl:
        return round(base_confidence, 4)

    decay = max(0.05, base_confidence * (ttl / (age + ttl)))
    return round(decay, 4)
