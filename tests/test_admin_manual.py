from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes_admin
from app.core.config import get_settings
from app.main import app
from app.services.manual_import_service import ManualImportService

client = TestClient(app)


def _use_temp_manual_service(monkeypatch, tmp_path: Path) -> ManualImportService:
    service = ManualImportService(tmp_path / "manual.csv")
    monkeypatch.setattr(routes_admin, "_manual_service", service)
    return service


def _valid_csv() -> str:
    return "\n".join(
        [
            "retailer,retailer_slug,product_name,alias,category,price,loyalty_price,available,postcode,source_url,last_checked_at,confidence",
            "Tesco,tesco,Semi-Skimmed Milk 2L,milk,Dairy,1.55,1.40,,SE13,,2026-05-14T10:00:00+00:00,0.7",
            "Tesco,tesco,Semi-Skimmed Milk 2L,milk,Dairy,1.50,1.35,,SE13,,2026-05-14T11:00:00+00:00,0.7",
            "Broken,broken,,bad,Other,0,,,,,,2.0",
        ]
    )


def test_get_manual_prices(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    response = client.get("/admin/manual-prices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_manual_prices_template(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    response = client.get("/admin/manual-prices/template")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "retailer,retailer_slug,product_name" in response.text
    assert "confidence" in response.text


def test_export_manual_prices(monkeypatch, tmp_path):
    service = _use_temp_manual_service(monkeypatch, tmp_path)
    service.import_csv_text(_valid_csv())
    response = client.get("/admin/manual-prices/export")
    assert response.status_code == 200
    assert "Semi-Skimmed Milk 2L" in response.text
    assert "confidence" in response.text


def test_import_manual_prices(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    payload = [
        {
            "retailer": "Test Retailer",
            "product_name": "Test Product",
            "price": 9.99,
            "confidence": 0.8,
        }
    ]
    response = client.post("/admin/manual-prices/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rows_imported"] == 1
    assert data["rows_skipped"] == 0


def test_validate_manual_prices_csv_reports_invalid_duplicate_and_stale(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    stale_csv = _valid_csv() + "\nAldi,aldi,Bananas,bananas,Fruit,0.89,,,,,2020-01-01T00:00:00+00:00,0.7"
    response = client.post(
        "/admin/manual-prices/validate-csv",
        content=stale_csv,
        headers={"content-type": "text/csv"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 4
    assert data["duplicate_rows"] == 1
    assert data["invalid_rows"] == 1
    assert data["missing_required_fields"] >= 1
    assert data["stale_rows"] == 1


def test_import_manual_prices_csv_skips_invalid_and_counts_duplicates(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    response = client.post(
        "/admin/manual-prices/import-csv",
        content=_valid_csv(),
        headers={"content-type": "text/csv"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 3
    assert data["rows_imported"] == 2
    assert data["rows_skipped"] == 1
    assert data["duplicate_rows"] >= 1
    assert data["invalid_rows"] == 1


def test_provider_priority():
    response = client.get("/admin/provider-priority")
    assert response.status_code == 200
    data = response.json()
    assert "priority_order" in data
    assert data["priority_order"] == ["manual_import", "open_prices", "tesco", "mock"]


def test_admin_auth_behavior(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    monkeypatch.setattr(get_settings(), "admin_token", "secret-test-token")

    response = client.get("/admin/manual-prices")
    assert response.status_code == 401

    response = client.get("/admin/manual-prices", headers={"X-Admin-Token": "wrong"})
    assert response.status_code == 401

    response = client.get("/admin/manual-prices", headers={"X-Admin-Token": "secret-test-token"})
    assert response.status_code == 200


def test_import_manual_prices_invalid_data(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    payload = [
        {
            "retailer": "",
            "product_name": "Test Product",
            "price": "free",
        }
    ]
    response = client.post("/admin/manual-prices/import", json=payload)
    assert response.status_code == 422


def test_admin_requires_token_in_production(monkeypatch, tmp_path):
    _use_temp_manual_service(monkeypatch, tmp_path)
    monkeypatch.setattr(get_settings(), "app_env", "production")
    monkeypatch.setattr(get_settings(), "admin_token", None)
    monkeypatch.setattr(get_settings(), "require_admin_token_in_production", True)

    response = client.get("/admin/manual-prices")
    assert response.status_code == 503
