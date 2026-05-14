"""Helpers for exposing daily web observation status in provider diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import get_settings
from app.db.database import SessionLocal, get_engine
from app.db.repositories import (
    PriceObservationRepository,
    ProviderRunRepository,
    WebPriceWatchlistRepository,
)
from app.services.scrapling_price_observation_service import get_scrapling_runtime


@dataclass(frozen=True)
class ObservationStatusSnapshot:
    daily_job_last_run_at: str | None
    enabled_watchlist_count: int
    enabled_url_count: int
    configured_url_count: int
    missing_url_count: int
    attempted_url_count: int
    observed_price_count: int
    successful_observations: int
    blocked_by_policy_count: int
    blocked_by_access_count: int
    blocked_count: int
    parse_failed_count: int
    internal_only_count: int
    last_report_path: str | None
    last_issue_url: str | None
    scrapling_enabled: bool
    scrapling_network_enabled: bool
    scrapling_available: bool
    scrapling_fetcher_available: bool
    scrapling_dynamic_fetcher_available: bool
    scrapling_stealthy_fetcher_available: bool
    scrapling_last_run_at: str | None
    scrapling_blocked_count: int
    scrapling_parse_failed_count: int
    scrapling_internal_only_count: int
    scrapling_public_eligible_count: int
    scrapling_warning: str | None
    last_attempted_urls: list[str] = field(default_factory=list)
    last_successful_observations: list[str] = field(default_factory=list)


def get_observation_status_snapshot() -> ObservationStatusSnapshot:
    settings = get_settings()
    (
        scrapling_available,
        fetcher_available,
        dynamic_fetcher_available,
        stealthy_fetcher_available,
        scrapling_import_error,
    ) = get_scrapling_runtime()

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        run_repo = ProviderRunRepository(db)
        watch_repo = WebPriceWatchlistRepository(db)
        observation_repo = PriceObservationRepository(db)

        last_run = run_repo.get_last_for_provider("daily_web_observation")
        scrapling_last_run = run_repo.get_last_for_provider("daily_scrapling_observation")
        enabled_count = watch_repo.count_enabled()
        enabled_url_count = watch_repo.count_enabled_with_url()
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
        attempted_urls = 0
        blocked_by_policy = 0
        blocked_by_access = 0
        blocked = 0
        parse_failed = 0
        internal_only = 0
        report_path: str | None = None
        issue_url: str | None = None
        last_run_at: str | None = None
        scrapling_last_run_at: str | None = None
        scrapling_blocked = 0
        scrapling_parse_failed = 0
        scrapling_internal_only = 0
        scrapling_public_eligible = 0

        if last_run is not None:
            last_run_at = (last_run.finished_at or last_run.started_at).isoformat()
            if last_run.message:
                try:
                    payload = json.loads(last_run.message)
                    attempted_urls = int(payload.get("urls_attempted", 0))
                    successful = int(payload.get("prices_observed", 0))
                    blocked_by_policy = int(payload.get("blocked_by_policy", 0))
                    blocked_by_access = int(payload.get("blocked_by_access", 0))
                    blocked = blocked_by_policy + blocked_by_access
                    parse_failed = int(payload.get("parse_failed", 0))
                    internal_only = int(payload.get("observations_internal_only", 0))
                    report_path = payload.get("report_path")
                    issue_url = payload.get("last_issue_url")
                except Exception:  # noqa: BLE001
                    pass

        if scrapling_last_run is not None:
            scrapling_last_run_at = (
                scrapling_last_run.finished_at or scrapling_last_run.started_at
            ).isoformat()
            if scrapling_last_run.message:
                try:
                    payload = json.loads(scrapling_last_run.message)
                    scrapling_blocked = int(payload.get("blocked_by_policy", 0)) + int(
                        payload.get("blocked_by_access", 0)
                    )
                    scrapling_parse_failed = int(payload.get("parse_failed", 0))
                    scrapling_internal_only = int(payload.get("internal_only", 0))
                    scrapling_public_eligible = int(payload.get("public_eligible", 0))
                except Exception:  # noqa: BLE001
                    pass

        if report_path is None:
            default_report = Path("artifacts/latest-price-observation-report.json")
            if default_report.exists():
                report_path = str(default_report)

        return ObservationStatusSnapshot(
            daily_job_last_run_at=last_run_at,
            enabled_watchlist_count=enabled_count,
            enabled_url_count=enabled_url_count,
            configured_url_count=configured_url_count,
            missing_url_count=missing_url_count,
            attempted_url_count=attempted_urls,
            observed_price_count=successful,
            successful_observations=successful,
            blocked_by_policy_count=blocked_by_policy,
            blocked_by_access_count=blocked_by_access,
            blocked_count=blocked,
            parse_failed_count=parse_failed,
            internal_only_count=internal_only,
            last_attempted_urls=last_attempted_urls,
            last_successful_observations=last_successful_observations,
            last_report_path=report_path,
            last_issue_url=issue_url,
            scrapling_enabled=settings.scrapling_enabled,
            scrapling_network_enabled=settings.scrapling_network_enabled,
            scrapling_available=scrapling_available,
            scrapling_fetcher_available=fetcher_available,
            scrapling_dynamic_fetcher_available=dynamic_fetcher_available,
            scrapling_stealthy_fetcher_available=stealthy_fetcher_available,
            scrapling_last_run_at=scrapling_last_run_at,
            scrapling_blocked_count=scrapling_blocked,
            scrapling_parse_failed_count=scrapling_parse_failed,
            scrapling_internal_only_count=scrapling_internal_only,
            scrapling_public_eligible_count=scrapling_public_eligible,
            scrapling_warning=(
                None
                if scrapling_available
                else f"Scrapling parser unavailable: {scrapling_import_error}"
            ),
        )
    finally:
        db.close()
