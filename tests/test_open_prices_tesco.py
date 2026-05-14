from __future__ import annotations

from app.providers.open_prices_provider import OpenPricesProvider
from app.providers.retailers.tesco_provider import TescoProvider


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", url="https://example.test"):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self.url = url

    def json(self):
        return self._payload


class FakeOpenPricesClient:
    def __init__(self, payload):
        self.payload = payload

    def get(self, *args, **kwargs):
        return FakeResponse(payload=self.payload, url="https://prices.openfoodfacts.org/api/v1/prices")


def test_open_prices_maps_gbp_price_and_keeps_stock_unknown(monkeypatch):
    def fake_off_get(*args, **kwargs):
        return FakeResponse(payload={"products": [{"code": "5000112546415", "product_name": "Milk"}]})

    provider = OpenPricesProvider()
    provider._client = FakeOpenPricesClient(
        {
            "items": [
                {
                    "price": "1.23",
                    "currency": "GBP",
                    "date": "2026-05-01",
                    "location_osm_name": "Community Shop",
                }
            ]
        }
    )
    monkeypatch.setattr("app.providers.open_prices_provider.httpx.get", fake_off_get)

    prices = provider.get_latest_prices(["milk"])

    assert len(prices) == 1
    price = prices[0]
    assert price.source == "open_prices"
    assert price.currency == "GBP"
    assert price.available is None
    assert price.confidence <= 0.6
    assert price.source_url


def test_open_prices_no_barcode_falls_back_without_crash(monkeypatch):
    def fake_off_get(*args, **kwargs):
        return FakeResponse(payload={"products": []})

    provider = OpenPricesProvider()
    monkeypatch.setattr("app.providers.open_prices_provider.httpx.get", fake_off_get)

    assert provider.get_latest_prices(["unknown thing"]) == []
    assert "No OpenFoodFacts barcode" in " ".join(provider.limitations)


def test_tesco_limited_failure_does_not_crash(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(status_code=403, text="blocked", url="https://www.tesco.com/search")

    monkeypatch.setattr("app.providers.retailers.tesco_provider.httpx.get", fake_get)
    provider = TescoProvider()

    assert provider.get_latest_prices(["milk"]) == []
    status = provider.status()
    assert status.status == "limited"
    assert status.supports_stock is False


def test_tesco_limited_price_has_low_confidence_and_unknown_stock(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(
            text="milk semi skimmed Tesco product price £1.55",
            url="https://www.tesco.com/shop/en-GB/search?query=milk",
        )

    monkeypatch.setattr("app.providers.retailers.tesco_provider.httpx.get", fake_get)
    provider = TescoProvider()

    prices = provider.get_latest_prices(["milk"])

    assert len(prices) == 1
    price = prices[0]
    assert price.source == "tesco"
    assert price.confidence == 0.3
    assert price.available is None
    assert price.source_url.startswith("https://www.tesco.com")
