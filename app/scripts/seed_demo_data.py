#!/usr/bin/env python3
"""
seed_demo_data.py — Demo verilerini veritabanına ekler.

Kullanım:
    python -m app.scripts.seed_demo_data
"""

from __future__ import annotations

import sys
from pathlib import Path

# Proje kökünü Python path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.database import init_db
from app.db.seed import seed_all


def main() -> None:
    print("Veritabanı başlatılıyor...")
    init_db()
    print("Demo verisi ekleniyor...")
    seed_all()
    print("✓ Seed tamamlandı.")


if __name__ == "__main__":
    main()
