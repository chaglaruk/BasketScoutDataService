#!/usr/bin/env python3
"""
provider_probe.py — Provider'ları manuel olarak test eder.

Kullanım:
    python -m app.scripts.provider_probe
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.provider_registry import get_registry


def main() -> None:
    registry = get_registry()
    statuses = registry.all_statuses()
    print(f"\nProvider Durumları ({len(statuses)} provider)\n{'=' * 50}")
    for s in statuses:
        icon = {"ok": "✓", "limited": "~", "blocked": "✗", "error": "!"}.get(s.status, "?")
        print(f"  {icon} [{s.status.upper():8}] {s.name} ({s.type})")
        if s.message:
            print(f"           {s.message}")
        for lim in s.limitations[:2]:
            print(f"           ⚠ {lim}")
    print()


if __name__ == "__main__":
    main()
