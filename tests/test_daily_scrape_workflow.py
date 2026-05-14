from __future__ import annotations

import json
from pathlib import Path


def test_daily_scrape_workflow_has_schedule_and_dispatch():
    workflow = Path('.github/workflows/daily-scrape.yml').read_text(encoding='utf-8')

    assert 'schedule:' in workflow
    assert "cron: '0 4 * * *'" in workflow
    assert 'workflow_dispatch:' in workflow
    assert 'dry_run:' in workflow


def test_daily_scrape_workflow_uploads_artifact():
    workflow = Path('.github/workflows/daily-scrape.yml').read_text(encoding='utf-8')

    assert 'actions/upload-artifact@v4' in workflow
    assert 'data/scraped_prices.json' in workflow


def test_scrapling_provider_writes_json(tmp_path):
    from app.providers.scrapling_provider import run_full_scrape

    out = tmp_path / 'scraped_prices.json'
    stats = run_full_scrape(
        retailers=['tesco'],
        queries=['milk'],
        output_path=str(out),
    )

    assert out.exists()
    payload = json.loads(out.read_text(encoding='utf-8'))
    assert 'stats' in payload
    assert 'products' in payload
    assert "started_at" in stats
