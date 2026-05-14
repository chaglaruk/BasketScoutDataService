from __future__ import annotations

from pathlib import Path


def test_daily_workflow_has_schedule_and_dispatch_and_permissions():
    workflow = Path('.github/workflows/daily-price-observation.yml').read_text(encoding='utf-8')

    assert 'schedule:' in workflow
    assert 'cron:' in workflow
    assert 'workflow_dispatch:' in workflow
    assert 'permissions:' in workflow
    assert 'issues: write' in workflow
    assert 'contents: write' in workflow
    assert 'actions: read' in workflow


def test_daily_workflow_uploads_artifacts_and_creates_issue():
    workflow = Path('.github/workflows/daily-price-observation.yml').read_text(encoding='utf-8')

    assert 'actions/upload-artifact@v4' in workflow
    assert 'Create or update attention issue' in workflow
    assert 'BasketScout daily price observation needs attention' in workflow
    assert 'retailer=${item.retailer}' in workflow
    assert 'product=${item.product}' in workflow
    assert 'url=${item.url' in workflow
    assert 'suggested_safe_action=${item.suggested_safe_action}' in workflow
