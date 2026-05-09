"""test_cache_policy.py — Cache politikası testleri."""
from __future__ import annotations

from datetime import timedelta

from app.core.time import utcnow
from app.domain.models import PriceItem
from app.services.cache_policy import (
    annotate_staleness,
    determine_data_mode,
    is_availability_stale,
    is_price_stale,
)


def make_price_item(source: str = "mock", is_stale: bool = False,
                    hours_ago: int = 0) -> PriceItem:
    lc = utcnow() - timedelta(hours=hours_ago)
    return PriceItem(
        retailer="Test",
        retailer_slug="test",
        product="milk",
        price=1.50,
        currency="GBP",
        source=source,
        last_checked_at=lc,
        confidence=1.0,
        is_stale=is_stale,
    )


def test_fresh_price_not_stale():
    now = utcnow()
    assert not is_price_stale(now)


def test_old_price_is_stale():
    old = utcnow() - timedelta(hours=25)
    assert is_price_stale(old)


def test_fresh_availability_not_stale():
    now = utcnow()
    assert not is_availability_stale(now)


def test_old_availability_is_stale():
    old = utcnow() - timedelta(hours=2)
    assert is_availability_stale(old)


def test_annotate_staleness_fresh():
    items = [make_price_item(hours_ago=0)]
    annotated, any_stale = annotate_staleness(items)
    assert not any_stale
    assert not annotated[0].is_stale


def test_annotate_staleness_old():
    items = [make_price_item(hours_ago=24)]
    annotated, any_stale = annotate_staleness(items)
    assert any_stale
    assert annotated[0].is_stale


def test_data_mode_mock():
    items = [make_price_item(source="mock")]
    assert determine_data_mode(items) == "mock"


def test_data_mode_mixed():
    items = [
        make_price_item(source="mock", is_stale=False),
        make_price_item(source="live", is_stale=True),
    ]
    assert determine_data_mode(items) == "mixed"


def test_data_mode_cache():
    items = [
        make_price_item(source="live", is_stale=True, hours_ago=24),
    ]
    # Stale olarak işaretle
    annotated = [i.model_copy(update={"is_stale": True}) for i in items]
    assert determine_data_mode(annotated) == "cache"


def test_data_mode_empty():
    assert determine_data_mode([]) == "mock"
