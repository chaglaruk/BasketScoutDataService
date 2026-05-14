#!/usr/bin/env python3
"""Run daily tracked web price observation job."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from app.services.scrapling_price_observation_service import run_scrapling_price_observation
from app.services.web_price_observation_service import run_daily_price_observation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=["default", "scrapling"],
        default="default",
        help="Observation backend: default (existing adapters) or scrapling (experimental lab).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Run without persisting observation rows.")
    parser.add_argument("--force", action="store_true", help="Ignore max_frequency_hours for this run.")
    args = parser.parse_args()

    try:
        if args.provider == "scrapling":
            report = run_scrapling_price_observation(dry_run=args.dry_run, force=args.force)
        else:
            report = run_daily_price_observation(dry_run=args.dry_run, force=args.force)
    except Exception as exc:  # noqa: BLE001
        print(f"[FATAL] daily web observation failed: {exc}")
        return 1

    payload = dataclasses.asdict(report)
    if "provider" not in payload:
        payload["provider"] = args.provider
    print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
