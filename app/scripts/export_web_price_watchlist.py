#!/usr/bin/env python3
"""Export current web price watchlist as CSV to stdout or file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.services.web_price_watchlist_io_service import export_watchlist_csv_text, template_csv_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None, help="Optional output path")
    parser.add_argument("--template", action="store_true", help="Export template instead of current rows")
    args = parser.parse_args()

    content = template_csv_text() if args.template else export_watchlist_csv_text()

    if args.output is None:
        sys.stdout.write(content)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        print(str(args.output))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
