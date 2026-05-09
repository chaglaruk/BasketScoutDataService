"""test_health.py — /health endpoint testi."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["service"] == "BasketScoutDataService"
    assert "version" in data
    assert "time" in data


def test_health_version_format():
    r = client.get("/health")
    version = r.json()["version"]
    # Basit versiyon formatı kontrolü
    parts = version.split(".")
    assert len(parts) >= 2
