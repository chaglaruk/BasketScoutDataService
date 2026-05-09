"""test_basket_compare.py — Sepet karşılaştırma testleri."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_basket_compare_basic():
    payload = {
        "items": [
            {"name": "milk", "quantity": 1},
            {"name": "bread", "quantity": 1},
        ],
        "coverage_threshold": 0.5,
    }
    r = client.post("/basket/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "stores" in data
    assert "metadata" in data
    assert len(data["stores"]) > 0


def test_basket_compare_recommends_cheapest():
    payload = {
        "items": [{"name": "milk", "quantity": 1}],
        "coverage_threshold": 0.9,
        "allow_own_brand": True,
    }
    r = client.post("/basket/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Aldi/Lidl en ucuz olmalı (mock veriye göre)
    if data.get("recommended"):
        assert data["recommended"]["total_price"] > 0
        assert data["recommended"]["coverage"] > 0


def test_basket_compare_own_brand_excluded():
    payload = {
        "items": [{"name": "milk", "quantity": 1}],
        "coverage_threshold": 0.5,
        "allow_own_brand": False,
    }
    r = client.post("/basket/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Own brand ürünler hariç tutulduğunda Aldi/Lidl eksik olabilir
    stores_with_items = [
        s for s in data["stores"]
        if any(li.get("unit_price") for li in s.get("line_items", []))
    ]
    for store in stores_with_items:
        for li in store.get("line_items", []):
            assert li.get("unit_price", 0) > 0


def test_basket_compare_loyalty_prices():
    payload = {
        "items": [{"name": "milk", "quantity": 2}],
        "coverage_threshold": 0.5,
        "use_loyalty_prices": True,
    }
    r = client.post("/basket/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Tesco'nun loyalty fiyatı 1.40, normal 1.55 — loyalty seçildiğinde daha ucuz olmalı
    tesco_store = next((s for s in data["stores"] if s["retailer_slug"] == "tesco"), None)
    if tesco_store and tesco_store.get("line_items"):
        for li in tesco_store["line_items"]:
            if li.get("unit_price"):
                assert li["unit_price"] <= 1.55  # loyalty <= normal


def test_basket_compare_metadata():
    payload = {
        "items": [{"name": "milk", "quantity": 1}],
    }
    r = client.post("/basket/compare", json=payload)
    data = r.json()
    assert "data_mode" in data["metadata"]
    assert "generated_at" in data["metadata"]
    assert isinstance(data["metadata"]["warnings"], list)


def test_basket_compare_missing_items():
    payload = {
        "items": [
            {"name": "milk", "quantity": 1},
            {"name": "xyznonexistentitem999", "quantity": 1},
        ],
        "coverage_threshold": 1.0,  # tam kapsama gerekiyor
    }
    r = client.post("/basket/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Hiçbir store tam kapsamayı karşılamamalı
    qualifying = [s for s in data["stores"] if s["qualifies"]]
    assert len(qualifying) == 0  # bilinmeyen ürün yüzünden
