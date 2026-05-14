from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import routes_prices
from app.main import app
from app.services.price_service import PriceQueryResult

client = TestClient(app)


class _EmptyPriceService:
    def get_latest(self, product_names, postcode=None, provider_names=None):  # noqa: ANN001
        return PriceQueryResult(items=[], any_stale=False, why_mock_used=None)


def test_provider_specific_empty_result_explains_limitation(monkeypatch):
    monkeypatch.setattr(routes_prices, "_service", _EmptyPriceService())

    response = client.get("/prices/latest?product=milk&provider=open_prices")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert "Provider 'open_prices' returned no price data" in data["warning"]
