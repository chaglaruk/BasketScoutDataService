#!/usr/bin/env python3
"""Import web price watchlist CSV into database."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.services.web_price_watchlist_io_service import import_watchlist_csv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--allow-short-frequency",
        action="store_true",
        help="Allow max_frequency_hours < 24 for dev-only scenarios.",
    )
    args = parser.parse_args()

    report = import_watchlist_csv(
        args.csv_path,
        allow_short_frequency=args.allow_short_frequency,
    )

    print(
        json.dumps(
            {
                "total_rows": report.total_rows,
                "rows_imported": report.rows_imported,
                "rows_skipped": report.rows_skipped,
                "invalid_rows": report.invalid_rows,
                "validation_issues": [
                    {
                        "row_number": issue.row_number,
                        "field": issue.field,
                        "message": issue.message,
                    }
                    for issue in report.validation_issues
                ],
            },
            indent=2,
        )
    )

    # Validation problems are reported but not fatal.
    return 0


if __name__ == "__main__":
    sys.exit(main())
