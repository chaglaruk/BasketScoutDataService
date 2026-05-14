"""Manual price feed management and CSV validation."""
from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.time import utcnow
from app.domain.models import (
    ManualCsvValidationIssue,
    ManualCsvValidationReport,
    ManualImportSummary,
    ManualPriceImportItem,
)
from app.domain.normalization import normalize_name

logger = logging.getLogger(__name__)

STALE_AFTER_DAYS = 30
HEADERS = [
    "retailer",
    "retailer_slug",
    "product_name",
    "alias",
    "category",
    "price",
    "loyalty_price",
    "available",
    "postcode",
    "source_url",
    "last_checked_at",
    "confidence",
]
REQUIRED_FIELDS = {"retailer", "product_name", "price"}
_RETAILER_DISPLAY_NAMES = {
    "tesco": "Tesco",
    "asda": "Asda",
    "sainsburys": "Sainsbury's",
    "aldi": "Aldi",
    "lidl": "Lidl",
    "morrisons": "Morrisons",
    "waitrose": "Waitrose",
    "coop": "Co-op",
    "iceland": "Iceland",
    "ocado": "Ocado",
    "mands": "M&S Food",
    "farmfoods": "Farmfoods",
}


class ManualImportService:
    def __init__(self, csv_path: Path = Path("data/manual_import/sample_prices.csv")) -> None:
        self._csv_path = csv_path

    def get_all(self) -> list[ManualPriceImportItem]:
        """Return all manual price rows from the configured CSV."""
        if not self._csv_path.exists():
            return []

        items: list[ManualPriceImportItem] = []
        with open(self._csv_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = _parse_row_to_item(row)
                if item is not None:
                    items.append(item)
        return items

    def import_items(self, items: list[ManualPriceImportItem]) -> ManualImportSummary:
        """Import JSON items and persist them to CSV. Last duplicate wins."""
        imported = 0
        skipped = 0
        duplicate_rows = 0
        errors: list[str] = []

        existing_items = self.get_all()
        data_map: dict[tuple[str, str, str], ManualPriceImportItem] = {
            _dedupe_key(i): i for i in existing_items
        }

        for item in items:
            row_errors = _validate_item(item)
            if row_errors:
                skipped += 1
                errors.extend(row_errors)
                continue

            normalized = _normalize_item(item)
            key = _dedupe_key(normalized)
            if key in data_map:
                duplicate_rows += 1
            data_map[key] = normalized
            imported += 1

        self._save_to_csv(list(data_map.values()))

        return ManualImportSummary(
            total_rows=len(items),
            rows_imported=imported,
            rows_skipped=skipped,
            duplicate_rows=duplicate_rows,
            invalid_rows=skipped,
            missing_required_fields=sum(1 for err in errors if "required" in err.lower()),
            stale_rows=sum(1 for item in items if _is_item_stale(item)),
            validation_errors=errors,
        )

    def validate_csv_text(self, csv_text: str) -> ManualCsvValidationReport:
        """Validate CSV text without writing anything."""
        rows, header_issues = _read_csv_rows(csv_text)
        report = ManualCsvValidationReport(total_rows=len(rows), issues=header_issues)
        seen: set[tuple[str, str, str]] = set()

        for index, row in enumerate(rows, start=2):
            row_issues = _validate_csv_row(row, index)
            item = _parse_row_to_item(row) if not row_issues else None
            if item is not None:
                key = _dedupe_key(item)
                if key in seen:
                    report.duplicate_rows += 1
                    row_issues.append(
                        ManualCsvValidationIssue(
                            row_number=index,
                            field=None,
                            message="Duplicate row; last row wins on import.",
                        )
                    )
                seen.add(key)
                if _is_item_stale(item):
                    report.stale_rows += 1
                    row_issues.append(
                        ManualCsvValidationIssue(
                            row_number=index,
                            field="last_checked_at",
                            message=f"Row is stale or missing last_checked_at (>{STALE_AFTER_DAYS} days).",
                        )
                    )

            missing_required = [issue for issue in row_issues if "required" in issue.message.lower()]
            report.missing_required_fields += len(missing_required)
            if any(_is_invalid_issue(issue) for issue in row_issues):
                report.invalid_rows += 1
            else:
                report.valid_rows += 1
            report.issues.extend(row_issues)

        return report

    def import_csv_text(self, csv_text: str) -> ManualImportSummary:
        """Validate and import CSV text. Invalid rows are skipped."""
        rows, header_issues = _read_csv_rows(csv_text)
        if header_issues:
            return ManualImportSummary(
                total_rows=len(rows),
                rows_imported=0,
                rows_skipped=len(rows),
                invalid_rows=len(rows),
                missing_required_fields=len(header_issues),
                validation_errors=[issue.message for issue in header_issues],
            )

        valid_items: list[ManualPriceImportItem] = []
        validation_errors: list[str] = []
        invalid_rows = 0
        missing_required = 0
        stale_rows = 0
        duplicate_rows = 0
        seen: set[tuple[str, str, str]] = set()

        for index, row in enumerate(rows, start=2):
            issues = [issue for issue in _validate_csv_row(row, index) if issue.field != "last_checked_at"]
            if issues:
                invalid_rows += 1
                missing_required += sum(1 for issue in issues if "required" in issue.message.lower())
                validation_errors.extend(f"Row {index}: {issue.message}" for issue in issues)
                continue
            item = _parse_row_to_item(row)
            if item is None:
                invalid_rows += 1
                validation_errors.append(f"Row {index}: unable to parse row")
                continue
            if item.last_checked_at is None:
                item = item.model_copy(update={"last_checked_at": utcnow()})
            if _is_item_stale(item):
                stale_rows += 1
            key = _dedupe_key(item)
            if key in seen:
                duplicate_rows += 1
            seen.add(key)
            valid_items.append(item)

        imported_summary = self.import_items(valid_items)
        return ManualImportSummary(
            total_rows=len(rows),
            rows_imported=imported_summary.rows_imported,
            rows_skipped=invalid_rows,
            duplicate_rows=duplicate_rows + imported_summary.duplicate_rows,
            invalid_rows=invalid_rows,
            missing_required_fields=missing_required,
            stale_rows=stale_rows,
            validation_errors=validation_errors,
        )

    def get_template_csv(self) -> str:
        """Return a CSV template string."""
        return ",".join(HEADERS) + "\n"

    def export_csv(self) -> str:
        """Export current manual prices as CSV text."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=HEADERS, lineterminator="\n")
        writer.writeheader()
        for item in self.get_all():
            writer.writerow(_item_to_row(item))
        return output.getvalue()

    def _save_to_csv(self, items: list[ManualPriceImportItem]) -> None:
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
            for item in sorted(items, key=lambda i: (_dedupe_key(i))):
                writer.writerow(_item_to_row(_normalize_item(item)))


def _read_csv_rows(csv_text: str) -> tuple[list[dict[str, str]], list[ManualCsvValidationIssue]]:
    if not csv_text.strip():
        return [], [ManualCsvValidationIssue(row_number=1, field=None, message="CSV body is empty.")]
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return [], [ManualCsvValidationIssue(row_number=1, field=None, message="CSV header row is missing.")]
    normalized_headers = {h.strip() for h in reader.fieldnames if h}
    missing = REQUIRED_FIELDS - normalized_headers
    issues = [
        ManualCsvValidationIssue(
            row_number=1,
            field=field,
            message=f"Missing required column: {field}",
        )
        for field in sorted(missing)
    ]
    return list(reader), issues


def _validate_csv_row(row: dict[str, str], row_number: int) -> list[ManualCsvValidationIssue]:
    issues: list[ManualCsvValidationIssue] = []
    for field in REQUIRED_FIELDS:
        if not (row.get(field) or "").strip():
            issues.append(
                ManualCsvValidationIssue(row_number=row_number, field=field, message=f"{field} is required.")
            )
    for field in ("price", "loyalty_price", "confidence"):
        raw = (row.get(field) or "").strip()
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            issues.append(ManualCsvValidationIssue(row_number=row_number, field=field, message=f"{field} must be numeric."))
            continue
        if field in {"price", "loyalty_price"} and value <= 0:
            issues.append(ManualCsvValidationIssue(row_number=row_number, field=field, message=f"{field} must be > 0."))
        if field == "confidence" and not 0 <= value <= 1:
            issues.append(ManualCsvValidationIssue(row_number=row_number, field=field, message="confidence must be between 0 and 1."))
    raw_date = (row.get("last_checked_at") or "").strip()
    if raw_date and _parse_datetime(raw_date) is None:
        issues.append(
            ManualCsvValidationIssue(row_number=row_number, field="last_checked_at", message="last_checked_at must be ISO-8601.")
        )
    return issues


def _is_invalid_issue(issue: ManualCsvValidationIssue) -> bool:
    if issue.field == "last_checked_at":
        return False
    return not (issue.field is None and issue.message.lower().startswith("duplicate row"))


def _parse_row_to_item(row: dict[str, str]) -> ManualPriceImportItem | None:
    try:
        price = float(row.get("price") or 0)
        if price <= 0:
            return None
        confidence = _parse_float(row.get("confidence"))
        return ManualPriceImportItem(
            retailer=_retailer_name(row),
            retailer_slug=_retailer_slug(row),
            product_name=(row.get("product_name") or "").strip(),
            alias=_blank_to_none(row.get("alias")),
            category=_blank_to_none(row.get("category")),
            price=price,
            loyalty_price=_parse_float(row.get("loyalty_price")),
            available=_parse_available(row.get("available")),
            postcode=_blank_to_none(row.get("postcode")),
            source_url=_blank_to_none(row.get("source_url")),
            last_checked_at=_parse_datetime(row.get("last_checked_at")),
            confidence=confidence,
        )
    except (ValueError, TypeError):
        return None


def _normalize_item(item: ManualPriceImportItem) -> ManualPriceImportItem:
    retailer = item.retailer.strip() if item.retailer else "Unknown"
    slug = item.retailer_slug or normalize_name(retailer)
    checked_at = item.last_checked_at or utcnow()
    confidence = item.confidence if item.confidence is not None else 0.7
    return item.model_copy(
        update={
            "retailer": retailer,
            "retailer_slug": slug,
            "product_name": item.product_name.strip(),
            "last_checked_at": checked_at,
            "confidence": confidence,
        }
    )


def _validate_item(item: ManualPriceImportItem) -> list[str]:
    errors: list[str] = []
    if not item.retailer.strip():
        errors.append("retailer is required")
    if not item.product_name.strip():
        errors.append("product_name is required")
    if item.price <= 0:
        errors.append("price must be > 0")
    if item.confidence is not None and not 0 <= item.confidence <= 1:
        errors.append("confidence must be between 0 and 1")
    return errors


def _item_to_row(item: ManualPriceImportItem) -> dict[str, str | float | None]:
    normalized = _normalize_item(item)
    return {
        "retailer": normalized.retailer,
        "retailer_slug": normalized.retailer_slug or normalize_name(normalized.retailer),
        "product_name": normalized.product_name,
        "alias": normalized.alias or "",
        "category": normalized.category or "",
        "price": normalized.price,
        "loyalty_price": normalized.loyalty_price if normalized.loyalty_price is not None else "",
        "available": _format_available(normalized.available),
        "postcode": normalized.postcode or "",
        "source_url": normalized.source_url or "",
        "last_checked_at": normalized.last_checked_at.isoformat() if normalized.last_checked_at else "",
        "confidence": normalized.confidence if normalized.confidence is not None else 0.7,
    }


def _dedupe_key(item: ManualPriceImportItem) -> tuple[str, str, str]:
    return (
        item.retailer_slug or normalize_name(item.retailer),
        normalize_name(item.product_name),
        (item.postcode or "").upper(),
    )


def _parse_available(raw: str | None) -> bool | None:
    normalized = (raw or "").strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    return None


def _format_available(value: bool | None) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return ""


def _parse_float(raw: str | None) -> float | None:
    if raw is None or not str(raw).strip():
        return None
    return float(str(raw).strip())


def _parse_datetime(raw: str | None) -> datetime | None:
    if raw is None or not str(raw).strip():
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _is_item_stale(item: ManualPriceImportItem) -> bool:
    if item.last_checked_at is None:
        return True
    checked = item.last_checked_at
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=UTC)
    return checked < utcnow() - timedelta(days=STALE_AFTER_DAYS)


def _blank_to_none(raw: str | None) -> str | None:
    value = (raw or "").strip()
    return value or None


def _retailer_slug(row: dict) -> str:
    slug = (row.get("retailer_slug") or "").strip()
    if slug:
        return slug
    return normalize_name((row.get("retailer") or "unknown").strip())


def _retailer_name(row: dict) -> str:
    name = (row.get("retailer") or "").strip()
    if name:
        return name
    slug = _retailer_slug(row)
    return _RETAILER_DISPLAY_NAMES.get(slug, slug.replace("_", " ").title() or "Unknown")
