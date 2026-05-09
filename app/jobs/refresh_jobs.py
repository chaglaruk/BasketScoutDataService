"""Zamanlanmış refresh görevleri."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def scheduled_refresh() -> None:
    """Zamanlanmış provider refresh görevi."""
    try:
        from app.services.refresh_service import RefreshService

        service = RefreshService()
        results = service.refresh_all()
        ok = sum(1 for r in results if r.get("status") == "ok")
        logger.info(f"Zamanlanmış refresh tamamlandı — {ok}/{len(results)} provider başarılı.")
    except Exception as exc:
        logger.error(f"Zamanlanmış refresh hatası: {exc}")
