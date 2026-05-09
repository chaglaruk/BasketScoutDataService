"""Zamanlanmış görev yöneticisi — APScheduler."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
    return _scheduler


def start_scheduler() -> None:
    """Scheduler'ı başlatır ve zamanlanmış görevleri ekler."""
    scheduler = get_scheduler()
    if scheduler.running:
        return

    from app.jobs.refresh_jobs import scheduled_refresh

    # Her 6 saatte bir mock dışı provider'ları yenile
    scheduler.add_job(
        scheduled_refresh,
        trigger=IntervalTrigger(hours=6),
        id="provider_refresh",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info("Scheduler başlatıldı — provider refresh görevi her 6 saatte bir.")


def stop_scheduler() -> None:
    """Scheduler'ı durdurur."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler durduruldu.")
