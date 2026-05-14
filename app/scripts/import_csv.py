"""Manual price feed CLI.

Usage:
    python -m app.scripts.import_csv validate data/manual_import/sample_prices.csv
    python -m app.scripts.import_csv import data/manual_import/sample_prices.csv
    python -m app.scripts.import_csv export artifacts/manual-export.csv
    python -m app.scripts.import_csv summary
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.services.manual_import_service import ManualImportService
from app.services.provider_registry import get_registry

DEFAULT_CSV = Path("data/manual_import/sample_prices.csv")


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    return path.read_text(encoding="utf-8-sig")


def cmd_validate(args: argparse.Namespace) -> int:
    service = ManualImportService(args.target)
    report = service.validate_csv_text(_read(args.csv_file))
    _print_json(_model_to_dict(report))
    return 1 if report.invalid_rows else 0


def cmd_import(args: argparse.Namespace) -> int:
    service = ManualImportService(args.target)
    summary = service.import_csv_text(_read(args.csv_file))
    _print_json(_model_to_dict(summary))
    return 1 if summary.invalid_rows else 0


def cmd_export(args: argparse.Namespace) -> int:
    service = ManualImportService(args.target)
    output = service.export_csv()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    _print_json({"exported_to": str(args.output), "rows": max(0, len(output.splitlines()) - 1)})
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    service = ManualImportService(args.target)
    items = service.get_all()
    sources = {}
    for item in items:
        slug = item.retailer_slug or item.retailer
        sources[slug] = sources.get(slug, 0) + 1
    statuses = [status.model_dump(mode="json") for status in get_registry().all_statuses()]
    _print_json({"manual_rows": len(items), "manual_rows_by_store": sources, "providers": statuses})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BasketScout manual price feed operations")
    parser.add_argument("--target", type=Path, default=DEFAULT_CSV, help="Target manual CSV path")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a manual CSV without importing")
    validate.add_argument("csv_file", type=Path)
    validate.set_defaults(func=cmd_validate)

    import_cmd = sub.add_parser("import", help="Import a manual CSV into the target feed")
    import_cmd.add_argument("csv_file", type=Path)
    import_cmd.set_defaults(func=cmd_import)

    export = sub.add_parser("export", help="Export the current target feed to CSV")
    export.add_argument("output", type=Path)
    export.set_defaults(func=cmd_export)

    summary = sub.add_parser("summary", help="Show manual feed and provider summary")
    summary.set_defaults(func=cmd_summary)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
