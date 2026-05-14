"""Helpers for exposing daily web observation status in provider diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.db.database import SessionLocal, get_engine
from app.db.repositories import (
    PriceObservationRepository,
    ProviderRunRepository,
    WebPriceWatchlistRepository,
)


@dataclass(frozen=True)
class ObservationStatusSnapshot:
    daily_job_last_run_at: str | None
    enabled_watchlist_count: int
    configured_url_count: int
    missing_url_count: int
    successful_observations: int
    blocked_count: int
    parse_failed_count: int
    internal_only_count: int
    last_report_path: str | None
    last_issue_url: str | None
    last_attempted_urls: list[str] = field(default_factory=list)
    last_successful_observations: list[str] = field(default_factory=list)


def get_observation_status_snapshot() -> ObservationStatusSnapshot:
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        run_repo = ProviderRunRepository(db)
        watch_repo = WebPriceWatchlistRepository(db)
        observation_repo = PriceObservationRepository(db)

        last_run = run_repo.get_last_for_provider("daily_web_observation")
        enabled_count = watch_repo.count_enabled()
        configured_url_count = watch_repo.count_with_url()
        missing_url_count = watch_repo.count_missing_url()
        last_attempted_urls = [
            row.product_url
            for row in watch_repo.get_recent_attempts(limit=10)
            if row.product_url
        ]
        last_successful_observations = [
            f"{row.retailer_slug}:{row.canonical_product_name}"
            for row in observation_repo.get_recent_success(limit=10)
        ]

        successful = 0
        blocked = 0
        parse_failed = 0
        internal_only = 0
        report_path: str | None = None
        issue_url: str | None = None
        last_run_at: str | None = None

        if last_run is not None:
            last_run_at = (last_run.finished_at or last_run.started_at).isoformat()
            if last_run.message:
                try:
                    payload = json.loads(last_run.message)
                    successful = int(payload.get("prices_observed", 0))
                    blocked = int(payload.get("blocked_by_policy", 0)) + int(
                        payload.get("blocked_by_access", 0)
                    )
                    parse_failed = int(payload.get("parse_failed", 0))
                    internal_only = int(payload.get("observations_internal_only", 0))
                    report_path = payload.get("report_path")
                    issue_url = payload.get("last_issue_url")
                except Exception:  # noqa: BLE001
                    pass

        if report_path is None:
            default_report = Path("artifacts/latest-price-observation-report.json")
            if default_report.exists():
                report_path = str(default_report)

        return ObservationStatusSnapshot(
            daily_job_last_run_at=last_run_at,
            enabled_watchlist_count=enabled_count,
            configured_url_count=configured_url_count,
            missing_url_count=missing_url_count,
            successful_observations=successful,
            blocked_count=blocked,
            parse_failed_count=parse_failed,
            internal_only_count=internal_only,
            last_attempted_urls=last_attempted_urls,
            last_successful_observations=last_successful_observations,
            last_report_path=report_path,
            last_issue_url=issue_url,
        )
    finally:
        db.close()
