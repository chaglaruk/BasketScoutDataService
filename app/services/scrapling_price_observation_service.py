"""Experimental Scrapling-based daily observation service (safe mode only)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

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
    AdapterObservationResult,
)
from app.services.web_price_observation_service import BLOCKED_BY_POLICY, _check_policy_and_robots

logger = logging.getLogger(__name__)

_BLOCK_PATTERNS = (
    "captcha",
    "access denied",
    "forbidden",
    "unusual traffic",
    "verify you are human",
    "bot",
    "challenge",
    "cloudflare",
)

_PRICE_PATTERNS = (
    re.compile(r"(?:\u00a3|gbp\s?)(\d{1,3}(?:\.\d{1,2})?)", re.IGNORECASE),
    re.compile(r"(\d{1,3}(?:\.\d{1,2})?)\s?(?:\u00a3|gbp)", re.IGNORECASE),
)

_PRICE_CSS_SELECTORS = (
    "meta[property='product:price:amount']::attr(content)",
    "meta[itemprop='price']::attr(content)",
    "[itemprop='price']::attr(content)",
    "[data-testid*='price']::text",
    ".price::text",
    ".product-price::text",
)


@dataclass
class FailureDetail:
    retailer: str
    product: str
    url: str
    failure_type: str
    suggested_safe_action: str
    error: str | None = None


@dataclass
class ScraplingObservationReport:
    started_at: str
    finished_at: str
    provider: str
    scrapling_enabled: bool
    scrapling_network_enabled: bool
    scrapling_available: bool
    fetcher_available: bool
    dynamic_fetcher_available: bool
    stealthy_fetcher_available: bool
    retailers_attempted: int
    urls_attempted: int
    prices_observed: int
    blocked_by_policy: int
    blocked_by_access: int
    parse_failed: int
    network_failed: int
    observations_published: int
    observations_internal_only: int
    public_eligible: int
    internal_only: int
    failure_details: list[dict[str, str | None]] = field(default_factory=list)
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


def _safe_action_for_failure(failure_type: str) -> str:
    if failure_type == BLOCKED_BY_POLICY:
        return "Keep row disabled and review robots/policy. Do not bypass restrictions."
    if failure_type == OUTCOME_BLOCKED_ACCESS:
        return "Treat retailer as blocked; do not attempt bypass/captcha/proxy/private API."
    if failure_type == OUTCOME_PARSE_FAILED:
        return "Review parser for this exact page structure or disable row if unstable."
    if failure_type == OUTCOME_NETWORK_FAILED:
        return "Retry on next schedule and verify endpoint reachability."
    return "Review safely; do not bypass access controls."


def get_scrapling_runtime() -> tuple[bool, bool, bool, bool, str | None]:
    try:
        from scrapling import Selector  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return False, False, False, False, str(exc)

    fetcher_available = False
    dynamic_fetcher_available = False
    stealthy_fetcher_available = False
    try:
        from scrapling.fetchers import DynamicFetcher, Fetcher, StealthyFetcher  # noqa: F401

        fetcher_available = True
        dynamic_fetcher_available = True
        stealthy_fetcher_available = True
    except Exception:  # noqa: BLE001
        # Parser can still be used even when fetcher extras are not installed.
        pass

    return True, fetcher_available, dynamic_fetcher_available, stealthy_fetcher_available, None


def parse_html_with_scrapling(
    *,
    page_html: str,
    source_url: str,
    expected_keywords: list[str],
    canonical_product_name: str,
) -> AdapterObservationResult:
    now = datetime.now(UTC)
    try:
        from scrapling import Selector
    except Exception as exc:  # noqa: BLE001
        return AdapterObservationResult(
            status=OUTCOME_NETWORK_FAILED,
            observed_at=now,
            captured_at=now,
            error_message=f"Scrapling not available: {exc}",
        )

    try:
        selector = Selector(content=page_html, url=source_url, adaptive=True)
    except Exception as exc:  # noqa: BLE001
        return AdapterObservationResult(
            status=OUTCOME_PARSE_FAILED,
            observed_at=now,
            captured_at=now,
            error_message=f"Scrapling parse failed: {exc}",
        )

    page_lower = page_html.lower()
    if any(marker in page_lower for marker in _BLOCK_PATTERNS):
        return AdapterObservationResult(
            status=OUTCOME_BLOCKED_ACCESS,
            observed_at=now,
            captured_at=now,
            error_message="Access-control marker detected in page content.",
        )

    raw_product_name = None
    try:
        title = selector.css("title::text").get()
        if title:
            raw_product_name = str(title).strip()
    except Exception:  # noqa: BLE001
        raw_product_name = None

    price_candidates: list[float] = []
    for css_selector in _PRICE_CSS_SELECTORS:
        try:
            values = selector.css(css_selector).getall()
        except Exception:  # noqa: BLE001
            continue
        for value in values:
            text = str(value).strip()
            for pattern in _PRICE_PATTERNS:
                for match in pattern.findall(text):
                    try:
                        price_candidates.append(float(match))
                    except ValueError:
                        continue

    for pattern in _PRICE_PATTERNS:
        for match in pattern.findall(page_html):
            try:
                price_candidates.append(float(match))
            except ValueError:
                continue

    if not price_candidates:
        return AdapterObservationResult(
            status=OUTCOME_PARSE_FAILED,
            observed_at=now,
            captured_at=now,
            raw_product_name=raw_product_name,
            parser_confidence=0.0,
            error_message="No GBP price pattern found.",
        )

    keywords = [kw.strip().lower() for kw in expected_keywords if kw.strip()]
    keyword_hits = sum(1 for keyword in keywords if keyword in page_lower)

    parser_confidence = 0.55
    if keywords and keyword_hits > 0:
        parser_confidence = 0.72
    elif canonical_product_name.lower() in page_lower:
        parser_confidence = 0.66

    warnings: list[str] = []
    if keywords and keyword_hits == 0:
        warnings.append("Expected product keywords were not found in page text.")

    return AdapterObservationResult(
        status=OUTCOME_SUCCESS,
        observed_at=now,
        captured_at=now,
        raw_product_name=raw_product_name,
        price_amount=price_candidates[0],
        loyalty_price_amount=None,
        parser_confidence=parser_confidence,
        warnings=warnings,
    )


def run_scrapling_price_observation(*, dry_run: bool = False, force: bool = False) -> ScraplingObservationReport:
    settings = get_settings()
    artifacts_dir, logs_dir = _ensure_dirs()
    report_path = artifacts_dir / "latest-price-observation-report.json"
    log_path = logs_dir / "latest-price-observation.log"
    _setup_file_logger(log_path)

    scrapling_available, fetcher_available, dynamic_available, stealthy_available, import_error = (
        get_scrapling_runtime()
    )

    start = utcnow()
    init_db()
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()

    provider_run_repo = ProviderRunRepository(db)
    watchlist_repo = WebPriceWatchlistRepository(db)
    observation_repo = PriceObservationRepository(db)

    run = provider_run_repo.create(
        provider_name="daily_scrapling_observation",
        provider_type="scrapling_observation",
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
    public_eligible = 0
    internal_only = 0
    failure_details: list[FailureDetail] = []
    warnings: list[str] = []
    errors: list[str] = []

    try:
        if not settings.scrapling_enabled:
            warnings.append("Scrapling provider is disabled by configuration.")
        if settings.scrapling_enabled and not scrapling_available:
            warnings.append(f"Scrapling parser is unavailable: {import_error}")

        watch_rows = watchlist_repo.get_enabled()
        if not watch_rows:
            warnings.append("No enabled watchlist rows. Nothing to observe.")

        if settings.scrapling_enabled and scrapling_available:
            for row in watch_rows:
                attempted_retailers.add(row.retailer_slug)

                if not row.product_url:
                    blocked_by_policy += 1
                    row.last_attempt_at = utcnow()
                    row.last_error = "No product_url configured."
                    row.policy_status = "unconfigured"
                    failure_details.append(
                        FailureDetail(
                            retailer=row.retailer_slug,
                            product=row.canonical_product_name,
                            url="",
                            failure_type=BLOCKED_BY_POLICY,
                            suggested_safe_action=_safe_action_for_failure(BLOCKED_BY_POLICY),
                            error=row.last_error,
                        )
                    )
                    continue

                if (not force) and (not _is_frequency_allowed(row.last_attempt_at, row.max_frequency_hours)):
                    warnings.append(
                        f"Skipped {row.retailer_slug}/{row.canonical_product_name}: max_frequency_hours not elapsed."
                    )
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
                    failure_details.append(
                        FailureDetail(
                            retailer=row.retailer_slug,
                            product=row.canonical_product_name,
                            url=row.product_url,
                            failure_type=BLOCKED_BY_POLICY,
                            suggested_safe_action=_safe_action_for_failure(BLOCKED_BY_POLICY),
                            error=policy_reason,
                        )
                    )
                    continue

                row.policy_status = "allowed"
                row.last_attempt_at = utcnow()
                urls_attempted += 1

                if dry_run:
                    warnings.append("Dry-run mode: no network call was made.")
                    continue

                if not settings.scrapling_network_enabled:
                    network_failed += 1
                    row.last_error = "SCRAPLING_NETWORK_ENABLED=false"
                    failure_details.append(
                        FailureDetail(
                            retailer=row.retailer_slug,
                            product=row.canonical_product_name,
                            url=row.product_url,
                            failure_type=OUTCOME_NETWORK_FAILED,
                            suggested_safe_action=_safe_action_for_failure(OUTCOME_NETWORK_FAILED),
                            error=row.last_error,
                        )
                    )
                    continue

                try:
                    response = httpx.get(
                        row.product_url,
                        headers={"User-Agent": settings.web_observation_user_agent},
                        timeout=settings.scrapling_timeout_seconds,
                        follow_redirects=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    network_failed += 1
                    row.last_error = str(exc)
                    failure_details.append(
                        FailureDetail(
                            retailer=row.retailer_slug,
                            product=row.canonical_product_name,
                            url=row.product_url,
                            failure_type=OUTCOME_NETWORK_FAILED,
                            suggested_safe_action=_safe_action_for_failure(OUTCOME_NETWORK_FAILED),
                            error=row.last_error,
                        )
                    )
                    continue

                if response.status_code in {401, 403, 429}:
                    blocked_by_access += 1
                    row.last_error = f"HTTP {response.status_code}"
                    row.policy_status = "blocked_by_access_control"
                    failure_details.append(
                        FailureDetail(
                            retailer=row.retailer_slug,
                            product=row.canonical_product_name,
                            url=row.product_url,
                            failure_type=OUTCOME_BLOCKED_ACCESS,
                            suggested_safe_action=_safe_action_for_failure(OUTCOME_BLOCKED_ACCESS),
                            error=row.last_error,
                        )
                    )
                    continue

                parsed = parse_html_with_scrapling(
                    page_html=response.text or "",
                    source_url=row.product_url,
                    expected_keywords=_parse_keywords(row.expected_product_keywords),
                    canonical_product_name=row.canonical_product_name,
                )

                if parsed.status == OUTCOME_SUCCESS and parsed.price_amount is not None:
                    prices_observed += 1
                    can_publish = bool(
                        row.public_display_allowed
                        and parsed.parser_confidence >= settings.scrapling_public_confidence_threshold
                    )
                    rights_status = "public_allowed" if can_publish else "internal_review_required"
                    if can_publish:
                        observations_published += 1
                        public_eligible += 1
                    else:
                        observations_internal_only += 1
                        internal_only += 1

                    observation_repo.add(
                        PriceObservation(
                            watchlist_id=row.id,
                            run_id=run.id,
                            retailer_slug=row.retailer_slug,
                            retailer_name=row.retailer_name,
                            canonical_product_name=row.canonical_product_name,
                            raw_product_name=parsed.raw_product_name,
                            price_amount=parsed.price_amount,
                            currency="GBP",
                            loyalty_price_amount=parsed.loyalty_price_amount,
                            observed_at=parsed.observed_at,
                            captured_at=parsed.captured_at,
                            provider_used=f"scrapling_observation_{row.retailer_slug}",
                            data_mode="observed_web_price",
                            confidence_score=min(max(parsed.parser_confidence, 0.0), 1.0),
                            freshness_bucket="fresh_24h",
                            source_url=row.product_url,
                            stock_status="Unknown",
                            warnings="; ".join(parsed.warnings) if parsed.warnings else None,
                            parser_confidence=min(max(parsed.parser_confidence, 0.0), 1.0),
                            public_display_allowed=can_publish,
                            rights_status=rights_status,
                            raw_snippet_hash=parsed.raw_snippet_hash,
                            outcome_status=OUTCOME_SUCCESS,
                            error_type=None,
                            error_message=None,
                        )
                    )
                    row.last_success_at = utcnow()
                    row.last_error = None
                    continue

                if parsed.status == OUTCOME_BLOCKED_ACCESS:
                    blocked_by_access += 1
                    row.last_error = parsed.error_message or "Access blocked"
                    row.policy_status = "blocked_by_access_control"
                elif parsed.status == OUTCOME_PARSE_FAILED:
                    parse_failed += 1
                    row.last_error = parsed.error_message or "Parse failed"
                else:
                    network_failed += 1
                    row.last_error = parsed.error_message or "Unknown parser failure"

                if parsed.warnings:
                    warnings.extend(parsed.warnings)
                failure_details.append(
                    FailureDetail(
                        retailer=row.retailer_slug,
                        product=row.canonical_product_name,
                        url=row.product_url,
                        failure_type=parsed.status,
                        suggested_safe_action=_safe_action_for_failure(parsed.status),
                        error=row.last_error,
                    )
                )

        finish = utcnow()
        status = "success"
        if (
            warnings
            or blocked_by_policy
            or blocked_by_access
            or parse_failed
            or network_failed
            or errors
        ):
            status = "partial"

        report = ScraplingObservationReport(
            started_at=start.isoformat(),
            finished_at=finish.isoformat(),
            provider="scrapling",
            scrapling_enabled=settings.scrapling_enabled,
            scrapling_network_enabled=settings.scrapling_network_enabled,
            scrapling_available=scrapling_available,
            fetcher_available=fetcher_available,
            dynamic_fetcher_available=dynamic_available,
            stealthy_fetcher_available=stealthy_available,
            retailers_attempted=len(attempted_retailers),
            urls_attempted=urls_attempted,
            prices_observed=prices_observed,
            blocked_by_policy=blocked_by_policy,
            blocked_by_access=blocked_by_access,
            parse_failed=parse_failed,
            network_failed=network_failed,
            observations_published=observations_published,
            observations_internal_only=observations_internal_only,
            public_eligible=public_eligible,
            internal_only=internal_only,
            failure_details=[asdict(item) for item in failure_details],
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
                    "provider": "scrapling",
                    "scrapling_enabled": settings.scrapling_enabled,
                    "scrapling_network_enabled": settings.scrapling_network_enabled,
                    "scrapling_available": scrapling_available,
                    "fetcher_available": fetcher_available,
                    "dynamic_fetcher_available": dynamic_available,
                    "stealthy_fetcher_available": stealthy_available,
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
                    "public_eligible": public_eligible,
                    "internal_only": internal_only,
                    "last_issue_url": None,
                    "dry_run": dry_run,
                    "failure_details": [asdict(item) for item in failure_details],
                }
            ),
        )

        if dry_run:
            db.rollback()
        else:
            db.commit()

        report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        logger.info("Scrapling observation completed. Report: %s", report_path)
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
            message=json.dumps({"fatal_error": str(exc), "provider": "scrapling"}),
        )
        db.commit()
        report = ScraplingObservationReport(
            started_at=start.isoformat(),
            finished_at=finish.isoformat(),
            provider="scrapling",
            scrapling_enabled=settings.scrapling_enabled,
            scrapling_network_enabled=settings.scrapling_network_enabled,
            scrapling_available=scrapling_available,
            fetcher_available=fetcher_available,
            dynamic_fetcher_available=dynamic_available,
            stealthy_fetcher_available=stealthy_available,
            retailers_attempted=len(attempted_retailers),
            urls_attempted=urls_attempted,
            prices_observed=prices_observed,
            blocked_by_policy=blocked_by_policy,
            blocked_by_access=blocked_by_access,
            parse_failed=parse_failed,
            network_failed=network_failed,
            observations_published=observations_published,
            observations_internal_only=observations_internal_only,
            public_eligible=public_eligible,
            internal_only=internal_only,
            failure_details=[asdict(item) for item in failure_details],
            warnings=warnings,
            errors=errors,
        )
        report_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        raise
    finally:
        db.close()


def report_to_dict(report: ScraplingObservationReport) -> dict[str, Any]:
    return asdict(report)

