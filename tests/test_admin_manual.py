from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_get_manual_prices():
    response = client.get("/admin/manual-prices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_manual_prices_template():
    response = client.get("/admin/manual-prices/template")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "retailer,retailer_slug,product_name" in response.text

def test_import_manual_prices():
    payload = [
        {
            "retailer": "Test Retailer",
            "product_name": "Test Product",
            "price": 9.99
        }
    ]
    response = client.post("/admin/manual-prices/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rows_imported"] == 1
    assert data["rows_skipped"] == 0

def test_provider_priority():
    response = client.get("/admin/provider-priority")
    assert response.status_code == 200
    data = response.json()
    assert "priority_order" in data
    assert data["priority_order"] == ["manual_import", "open_prices", "tesco", "mock"]
