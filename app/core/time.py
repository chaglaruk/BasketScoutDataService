"""Zaman yardımcı fonksiyonları."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware UTC şu anki zamanı döndürür."""
    return datetime.now(UTC)


def seconds_since(dt: datetime) -> float:
    """Verilen datetime'dan bu yana geçen saniye sayısını döndürür."""
    return (utcnow() - dt).total_seconds()


def is_stale(dt: datetime, ttl_seconds: int) -> bool:
    """Verilen datetime TTL süresini aşmışsa True döndürür."""
    return seconds_since(dt) > ttl_seconds
