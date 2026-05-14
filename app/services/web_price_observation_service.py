"""Daily tracked web price observation workflow service."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.core.time import utcnow
from app.db.database import SessionLocal, get_engine, init_db
from app.db.models import PriceObservation
from app.db.repositories import (
    PriceObservationRepository,
    ProviderRunRepository,
    WebPriceWatchlistRepository,
)
from app.providers.web_observation_adapters import (
    OUTCOME_BLOCKED_ACCESS,
    OUTCOME_NETWORK_FAILED,
    OUTCOME_PARSE_FAILED,
    OUTCOME_SUCCESS,
    AldiWebObservationAdapter,
    LidlWebObservationAdapter,
    SainsburyWebObservationAdapter,
    TescoWebObservationAdapter,
)

logger = logging.getLogger(__name__)

BLOCKED_BY_POLICY = "BLOCKED_BY_ROBOTS_OR_POLICY"


@dataclass
class ObservationReport:
    started_at: str
    finished_at: str
    retailers_attempted: int
    urls_attempted: int
    prices_observed: int
    blocked_by_policy: int
    blocked_by_access: int
    parse_failed: int
    network_failed: int
    observations_published: int
    observations_internal_only: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _ensure_dirs() -> tuple[Path, Path]:
    artifacts_dir = Path("artifacts")
    logs_dir = Path("logs")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir, logs_dir


def _setup_file_logger(log_path: Path) -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)


def _parse_keywords(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _is_frequency_allowed(last_attempt_at: datetime | None, max_frequency_hours: int) -> bool:
    if last_attempt_at is None:
        return True
    if last_attempt_at.tzinfo is None:
        last_attempt_at = last_attempt_at.replace(tzinfo=UTC)
    threshold = utcnow() - timedelta(hours=max_frequency_hours)
    return last_attempt_at <= threshold


def _check_policy_and_robots(product_url: str, user_agent: str) -> tuple[bool, str]:
    parsed = urlparse(product_url)
    if parsed.scheme not in {"http", "https"}:
        return False, "URL must be http/https."
    if not parsed.netloc:
        return False, "URL host is missing."

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        req = Request(robots_url, headers={"User-Agent": user_agent})
        with urlopen(req, timeout=10) as resp:  # noqa: S310
            robots_body = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        return False, f"robots.txt fetch failed: {exc}"

    disallow_all = False
    user_agent_match = False
    for line in robots_body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        low = stripped.lower()
        if low.startswith("user-agent:"):
            agent_value = low.split(":", 1)[1].strip()
            user_agent_match = agent_value in {"*", user_agent.lower()}
            continue
        if user_agent_match and low.startswith("disallow:"):
            path = low.split(":", 1)[1].strip()
            if path == "/":
                disallow_all = True
                break
            if path and parsed.path.startswith(path):
                return False, f"robots.txt disallows path prefix {path}"

    if disallow_all:
        return False, "robots.txt disallows crawling for this user-agent."
    return True, "allowed"


def _adapter_for_slug(slug: str, timeout_seconds: float, user_agent: str):
    if slug == "tesco":
        return TescoWebObservationAdapter(timeout_seconds=timeout_seconds, user_agent=user_agent)
    if slug == "aldi":
        return AldiWebObservationAdapter(timeout_seconds=timeout_seconds, user_agent=user_agent)
    if slug == "sainsburys":
        return SainsburyWebObservationAdapter(timeout_seconds=timeout_seconds, user_agent=user_agent)
    if slug == "lidl":
        return LidlWebObservationAdapter(timeout_seconds=timeout_seconds, user_agent=user_agent)
    return None


def run_daily_price_observation(*, dry_run: bool = False, force: bool = False) -> ObservationReport:
    settings = get_settings()
    artifacts_dir, logs_dir = _ensure_dirs()
    report_path = artifacts_dir / "latest-price-observation-report.json"
    log_path = logs_dir / "latest-price-observation.log"
    _setup_file_logger(log_path)

    start = utcnow()
    init_db()

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()

    provider_run_repo = ProviderRunRepository(db)
    watchlist_repo = WebPriceWatchlistRepository(db)
    observation_repo = PriceObservationRepository(db)

    run = provider_run_repo.create(
        provider_name="daily_web_observation",
        provider_type="web_observation",
        started_at=start,
    )

    attempted_retailers: set[str] = set()
    urls_attempted = 0
    prices_observed = 0
    blocked_by_policy = 0
    blocked_by_access = 0
    parse_failed = 0
    network_failed = 0
    observations_published = 0
    observations_internal_only = 0
    warnings: list[str] = []
    errors: list[str] = []

    try:
        if not settings.web_observation_enabled:
            warnings.append("Web observation is disabled by configuration.")
            finish = utcnow()
            report = ObservationReport(
                started_at=start.isoformat(),
                finished_at=finish.isoformat(),
                retailers_attempted=0,
                urls_attempted=0,
                prices_observed=0,
                blocked_by_policy=0,
                blocked_by_access=0,
                parse_failed=0,
                network_failed=0,
                observations_published=0,
                observations_internal_only=0,
                warnings=warnings,
                errors=errors,
            )
            provider_run_repo.finish(
                run,
                status="partial",
                finished_at=finish,
                products_checked=0,
                prices_found=0,
                errors_count=0,
                message=json.dumps({"report_path": str(report_path), "warnings": warnings}),
            )
            db.commit()
            report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
            return report

        watch_rows = watchlist_repo.get_enabled()
        if not watch_rows:
            warnings.append("No enabled watchlist rows. Nothing to observe.")

        for row in watch_rows:
            attempted_retailers.add(row.retailer_slug)

            if not row.product_url:
                blocked_by_policy += 1
                row.last_attempt_at = utcnow()
                row.last_error = "No product_url configured."
                row.policy_status = "unconfigured"
                continue

            if (not force) and (not _is_frequency_allowed(row.last_attempt_at, row.max_frequency_hours)):
                warnings.append(
                    f"Skipped {row.retailer_slug}/{row.canonical_product_name}: max_frequency_hours not elapsed."
                )
                continue

            adapter = _adapter_for_slug(
                row.retailer_slug,
                timeout_seconds=settings.web_observation_timeout_seconds,
                user_agent=settings.web_observation_user_agent,
            )
            if adapter is None:
                blocked_by_policy += 1
                row.last_attempt_at = utcnow()
                row.last_error = f"No adapter for retailer slug '{row.retailer_slug}'."
                row.policy_status = "blocked_by_policy"
                continue

            allowed, policy_reason = _check_policy_and_robots(
                row.product_url,
                settings.web_observation_user_agent,
            )
            row.robots_checked_at = utcnow()
            if not allowed:
                blocked_by_policy += 1
                row.policy_status = "blocked_by_policy"
                row.last_attempt_at = utcnow()
                row.last_error = policy_reason
                warnings.append(
                    f"Policy blocked {row.retailer_slug}/{row.canonical_product_name}: {policy_reason}"
                )
                continue

            row.policy_status = "allowed"
            row.last_attempt_at = utcnow()
            urls_attempted += 1

            result = adapter.observe(
                product_url=row.product_url,
                expected_keywords=_parse_keywords(row.expected_product_keywords),
                canonical_product_name=row.canonical_product_name,
                dry_run=dry_run,
            )

            if result.status == OUTCOME_SUCCESS and result.price_amount is not None:
                prices_observed += 1
                if row.public_display_allowed:
                    observations_published += 1
                    rights_status = "public_allowed"
                else:
                    observations_internal_only += 1
                    rights_status = "internal_only"

                if not dry_run:
                    observation_repo.add(
                        PriceObservation(
                            watchlist_id=row.id,
                            run_id=run.id,
                            retailer_slug=row.retailer_slug,
                            retailer_name=row.retailer_name,
                            canonical_product_name=row.canonical_product_name,
                            raw_product_name=result.raw_product_name,
                            price_amount=result.price_amount,
                            currency="GBP",
                            loyalty_price_amount=result.loyalty_price_amount,
                            observed_at=result.observed_at,
                            captured_at=result.captured_at,
                            provider_used=f"web_observation_{row.retailer_slug}",
                            data_mode="observed_web_price",
                            confidence_score=min(max(result.parser_confidence, 0.0), 1.0),
                            freshness_bucket="fresh_24h",
                            source_url=row.product_url,
                            stock_status="Unknown",
                            warnings="; ".join(result.warnings) if result.warnings else None,
                            parser_confidence=min(max(result.parser_confidence, 0.0), 1.0),
                            public_display_allowed=row.public_display_allowed,
                            rights_status=rights_status,
                            raw_snippet_hash=result.raw_snippet_hash,
                            outcome_status=OUTCOME_SUCCESS,
                            error_type=None,
                            error_message=None,
                        )
                    )
                row.last_success_at = utcnow()
                row.last_error = None
                continue

            if result.status == OUTCOME_BLOCKED_ACCESS:
                blocked_by_access += 1
                row.last_error = result.error_message or "Access blocked"
                row.policy_status = "blocked_by_access_control"
            elif result.status == OUTCOME_NETWORK_FAILED:
                network_failed += 1
                row.last_error = result.error_message or "Network failure"
            elif result.status == OUTCOME_PARSE_FAILED:
                parse_failed += 1
                row.last_error = result.error_message or "Parse failed"
            else:
                network_failed += 1
                row.last_error = result.error_message or "Unknown adapter result"

            if result.warnings:
                warnings.extend(result.warnings)

        finish = utcnow()
        status = "success"
        if blocked_by_policy or blocked_by_access or parse_failed or network_failed:
            status = "partial"

        report = ObservationReport(
            started_at=start.isoformat(),
            finished_at=finish.isoformat(),
            retailers_attempted=len(attempted_retailers),
            urls_attempted=urls_attempted,
            prices_observed=prices_observed,
            blocked_by_policy=blocked_by_policy,
            blocked_by_access=blocked_by_access,
            parse_failed=parse_failed,
            network_failed=network_failed,
            observations_published=observations_published,
            observations_internal_only=observations_internal_only,
            warnings=warnings,
            errors=errors,
        )

        provider_run_repo.finish(
            run,
            status=status,
            finished_at=finish,
            products_checked=urls_attempted,
            prices_found=prices_observed,
            errors_count=(blocked_by_policy + blocked_by_access + parse_failed + network_failed),
            message=json.dumps(
                {
                    "report_path": str(report_path),
                    "retailers_attempted": len(attempted_retailers),
                    "urls_attempted": urls_attempted,
                    "prices_observed": prices_observed,
                    "blocked_by_policy": blocked_by_policy,
                    "blocked_by_access": blocked_by_access,
                    "parse_failed": parse_failed,
                    "network_failed": network_failed,
                    "observations_published": observations_published,
                    "observations_internal_only": observations_internal_only,
                    "last_issue_url": None,
                    "dry_run": dry_run,
                }
            ),
        )

        if dry_run:
            db.rollback()
        else:
            db.commit()

        report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        logger.info("Daily web observation completed. Report: %s", report_path)
        return report

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        finish = utcnow()
        errors.append(str(exc))
        provider_run_repo.finish(
            run,
            status="failed",
            finished_at=finish,
            products_checked=urls_attempted,
            prices_found=prices_observed,
            errors_count=(blocked_by_policy + blocked_by_access + parse_failed + network_failed + 1),
            message=json.dumps({"fatal_error": str(exc), "report_path": str(report_path)}),
        )
        db.commit()

        report = ObservationReport(
            started_at=start.isoformat(),
            finished_at=finish.isoformat(),
            retailers_attempted=len(attempted_retailers),
            urls_attempted=urls_attempted,
            prices_observed=prices_observed,
            blocked_by_policy=blocked_by_policy,
            blocked_by_access=blocked_by_access,
            parse_failed=parse_failed,
            network_failed=network_failed,
            observations_published=observations_published,
            observations_internal_only=observations_internal_only,
            warnings=warnings,
            errors=errors,
        )
        report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        raise
    finally:
        db.close()


def report_to_dict(report: ObservationReport) -> dict[str, Any]:
    return asdict(report)
