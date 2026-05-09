"""test_mock_provider.py — MockProvider testleri."""
from __future__ import annotations

import pytest

from app.providers.mock_provider import MockProvider


@pytest.fixture
def provider():
    return MockProvider()


def test_mock_status_ok(provider):
    status = provider.status()
    assert status.status == "ok"
    assert status.name == "mock"


def test_mock_search_milk(provider):
    results = provider.search_products("milk")
    assert len(results) > 0
    names = [r.canonical_name.lower() for r in results]
    assert any("milk" in n for n in names)


def test_mock_search_bread(provider):
    results = provider.search_products("bread")
    assert len(results) > 0


def test_mock_search_empty(provider):
    results = provider.search_products("xyznonexistentproduct123")
    assert results == []


def test_mock_prices_milk(provider):
    prices = provider.get_latest_prices(["milk"])
    assert len(prices) == 8  # 8 perakendeci
    retailers = {p.retailer_slug for p in prices}
    assert "tesco" in retailers
    assert "asda" in retailers
    assert "aldi" in retailers


def test_mock_prices_confidence(provider):
    prices = provider.get_latest_prices(["milk"])
    for p in prices:
        assert p.confidence == 1.0
        assert p.source == "mock"
        assert p.currency == "GBP"
        assert p.price > 0


def test_mock_prices_multiple_products(provider):
    prices = provider.get_latest_prices(["milk", "bread", "eggs"])
    assert len(prices) > 8  # birden fazla ürün


def test_mock_refresh(provider):
    result = provider.refresh_products()
    assert result["status"] == "ok"


def test_mock_type(provider):
    assert provider.type == "mock"
    assert provider.supports_live_prices is False
