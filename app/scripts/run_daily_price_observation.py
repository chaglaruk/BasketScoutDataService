#!/usr/bin/env python3
"""Run daily tracked web price observation job."""

from __future__ import annotations

import argparse
import json
import sys

from app.services.web_price_observation_service import run_daily_price_observation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run without persisting observation rows.")
    parser.add_argument("--force", action="store_true", help="Ignore max_frequency_hours for this run.")
    args = parser.parse_args()

    try:
        report = run_daily_price_observation(dry_run=args.dry_run, force=args.force)
    except Exception as exc:  # noqa: BLE001
        print(f"[FATAL] daily web observation failed: {exc}")
        return 1

    print(json.dumps({
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "retailers_attempted": report.retailers_attempted,
        "urls_attempted": report.urls_attempted,
        "prices_observed": report.prices_observed,
        "blocked_by_policy": report.blocked_by_policy,
        "blocked_by_access": report.blocked_by_access,
        "parse_failed": report.parse_failed,
        "network_failed": report.network_failed,
        "observations_published": report.observations_published,
        "observations_internal_only": report.observations_internal_only,
        "warnings": report.warnings,
        "errors": report.errors,
    }, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
