"""test_provider_status.py — Provider durum endpoint testleri."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_providers_status_endpoint():
    r = client.get("/providers/status")
    assert r.status_code == 200
    data = r.json()
    assert "providers" in data
    assert len(data["providers"]) >= 1


def test_mock_provider_in_status():
    r = client.get("/providers/status")
    data = r.json()
    provider_names = [p["name"] for p in data["providers"]]
    assert "mock" in provider_names


def test_provider_status_fields():
    r = client.get("/providers/status")
    data = r.json()
    for p in data["providers"]:
        assert "name" in p
        assert "status" in p
        assert "type" in p
        assert p["status"] in ("ok", "limited", "blocked", "error", "unknown")


def test_retailer_providers_limited():
    r = client.get("/providers/status")
    data = r.json()
    retailer_slugs = {"tesco", "asda", "sainsburys", "morrisons",
                      "waitrose", "coop", "aldi", "lidl"}
    for p in data["providers"]:
        if p["name"] in retailer_slugs:
            if p["name"] == "tesco":
                assert p["status"] in ("ok", "limited", "blocked", "error")
            else:
                assert p["status"] in ("limited", "blocked", "error")
