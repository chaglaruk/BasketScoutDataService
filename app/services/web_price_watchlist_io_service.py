"""CSV import/export utilities for web price watchlist."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from app.db.database import SessionLocal, get_engine, init_db
from app.db.repositories import WebPriceWatchlistRepository

WATCHLIST_HEADERS = [
    "retailer_slug",
    "retailer_name",
    "canonical_product_name",
    "product_url",
    "expected_product_keywords",
    "enabled",
    "max_frequency_hours",
    "policy_status",
    "public_display_allowed",
    "notes",
]


@dataclass
class WatchlistValidationIssue:
    row_number: int
    field: str | None
    message: str


@dataclass
class WatchlistImportReport:
    total_rows: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0
    invalid_rows: int = 0
    validation_issues: list[WatchlistValidationIssue] = field(default_factory=list)


@dataclass
class WatchlistRow:
    retailer_slug: str
    retailer_name: str
    canonical_product_name: str
    product_url: str | None
    expected_product_keywords: str | None
    enabled: bool
    max_frequency_hours: int
    policy_status: str
    public_display_allowed: bool
    notes: str | None


def template_csv_text() -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=WATCHLIST_HEADERS, lineterminator="\n")
    writer.writeheader()
    return output.getvalue()


def _to_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    value = str(raw).strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y"}


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_row(
    row: dict[str, str],
    row_number: int,
    allow_short_frequency: bool,
) -> tuple[WatchlistRow | None, list[WatchlistValidationIssue]]:
    issues: list[WatchlistValidationIssue] = []

    retailer_slug = (row.get("retailer_slug") or "").strip().lower()
    retailer_name = (row.get("retailer_name") or "").strip()
    canonical_product_name = (row.get("canonical_product_name") or "").strip()
    product_url_raw = (row.get("product_url") or "").strip()
    product_url = product_url_raw or None
    expected_keywords = (row.get("expected_product_keywords") or "").strip() or None
    enabled = _to_bool(row.get("enabled"), default=False)
    policy_status = (row.get("policy_status") or "unconfigured").strip() or "unconfigured"
    public_display_allowed = _to_bool(row.get("public_display_allowed"), default=False)
    notes = (row.get("notes") or "").strip() or None

    if not retailer_slug:
        issues.append(WatchlistValidationIssue(row_number, "retailer_slug", "retailer_slug is required"))
    if not canonical_product_name:
        issues.append(
            WatchlistValidationIssue(
                row_number,
                "canonical_product_name",
                "canonical_product_name is required",
            )
        )

    max_frequency_hours = 24
    raw_freq = (row.get("max_frequency_hours") or "").strip()
    if raw_freq:
        try:
            max_frequency_hours = int(raw_freq)
        except ValueError:
            issues.append(
                WatchlistValidationIssue(
                    row_number,
                    "max_frequency_hours",
                    "max_frequency_hours must be an integer",
                )
            )
    if max_frequency_hours < 24 and not allow_short_frequency:
        issues.append(
            WatchlistValidationIssue(
                row_number,
                "max_frequency_hours",
                "max_frequency_hours must be >= 24 unless --allow-short-frequency is used",
            )
        )

    if enabled and not product_url:
        issues.append(
            WatchlistValidationIssue(
                row_number,
                "product_url",
                "enabled=true requires product_url",
            )
        )
    if enabled and product_url and not _is_http_url(product_url):
        issues.append(
            WatchlistValidationIssue(
                row_number,
                "product_url",
                "product_url must be http/https when enabled=true",
            )
        )
    if product_url and not _is_http_url(product_url):
        issues.append(
            WatchlistValidationIssue(
                row_number,
                "product_url",
                "product_url must be http/https",
            )
        )

    if issues:
        return None, issues

    return (
        WatchlistRow(
            retailer_slug=retailer_slug,
            retailer_name=retailer_name or retailer_slug.replace("_", " ").title(),
            canonical_product_name=canonical_product_name,
            product_url=product_url,
            expected_product_keywords=expected_keywords,
            enabled=enabled,
            max_frequency_hours=max_frequency_hours,
            policy_status=policy_status,
            public_display_allowed=public_display_allowed,
            notes=notes,
        ),
        [],
    )


def import_watchlist_csv(path: Path, *, allow_short_frequency: bool = False) -> WatchlistImportReport:
    init_db()
    SessionLocal.configure(bind=get_engine())

    report = WatchlistImportReport()

    if not path.exists():
        report.validation_issues.append(
            WatchlistValidationIssue(1, "path", f"CSV file not found: {path}")
        )
        report.invalid_rows = 1
        report.rows_skipped = 1
        return report

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            report.validation_issues.append(
                WatchlistValidationIssue(1, None, "CSV header row is missing")
            )
            report.invalid_rows = 1
            report.rows_skipped = 1
            return report

        db = SessionLocal()
        repo = WebPriceWatchlistRepository(db)
        try:
            for row_number, row in enumerate(reader, start=2):
                report.total_rows += 1
                parsed, issues = _validate_row(row, row_number, allow_short_frequency)
                if issues:
                    report.rows_skipped += 1
                    report.invalid_rows += 1
                    report.validation_issues.extend(issues)
                    continue

                assert parsed is not None
                repo.upsert(
                    retailer_slug=parsed.retailer_slug,
                    retailer_name=parsed.retailer_name,
                    canonical_product_name=parsed.canonical_product_name,
                    product_url=parsed.product_url,
                    expected_product_keywords=parsed.expected_product_keywords,
                    enabled=parsed.enabled,
                    max_frequency_hours=parsed.max_frequency_hours,
                    policy_status=parsed.policy_status,
                    public_display_allowed=parsed.public_display_allowed,
                    notes=parsed.notes,
                )
                report.rows_imported += 1
            db.commit()
        finally:
            db.close()

    return report


def export_watchlist_csv_text() -> str:
    init_db()
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    try:
        rows = repo.get_all()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=WATCHLIST_HEADERS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "retailer_slug": row.retailer_slug,
                    "retailer_name": row.retailer_name,
                    "canonical_product_name": row.canonical_product_name,
                    "product_url": row.product_url or "",
                    "expected_product_keywords": row.expected_product_keywords or "",
                    "enabled": "true" if row.enabled else "false",
                    "max_frequency_hours": row.max_frequency_hours,
                    "policy_status": row.policy_status,
                    "public_display_allowed": "true" if row.public_display_allowed else "false",
                    "notes": row.notes or "",
                }
            )
        return output.getvalue()
    finally:
        db.close()
