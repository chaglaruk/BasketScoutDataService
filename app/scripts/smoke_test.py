#!/usr/bin/env python3
"""
smoke_test.py -- Servisin calistigini hizlica dogrular.

Kullanim:
    python -m app.scripts.smoke_test
    veya scripts/smoke.ps1
"""

from __future__ import annotations

import sys

import httpx

# Windows console encoding fix
if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp1254", "cp1252", "ascii"):
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8787"


def check(label: str, fn):
    try:
        fn()
        print(f"  [OK] {label}")
        return True
    except Exception as exc:
        print(f"  [FAIL] {label} -- {exc}")
        return False


def main() -> int:
    print(f"\nBasketScoutDataService Smoke Test -- {BASE}\n")
    passed = 0
    total = 0

    def test_health():
        r = httpx.get(f"{BASE}/health", timeout=20)
        r.raise_for_status()
        data = r.json()
        assert data["ok"] is True, f"ok!=True: {data}"

    def test_providers():
        r = httpx.get(f"{BASE}/providers/status", timeout=20.0)
        r.raise_for_status()
        data = r.json()
        assert "providers" in data
        assert len(data["providers"]) > 0

    def test_search():
        r = httpx.get(f"{BASE}/products/search?q=milk", timeout=20)
        r.raise_for_status()
        data = r.json()
        assert data["count"] > 0, f"Urun bulunamadi: {data}"

    def test_prices():
        r = httpx.get(f"{BASE}/prices/latest?product=milk", timeout=20.0)
        r.raise_for_status()
        data = r.json()
        prices = data.get("items", [])
        assert isinstance(prices, list), "Expected list of PriceItem in items"
        assert len(prices) > 0, "Fiyat bulunamadi"

        for p in prices:
            assert "source" in p, "Missing source field"
            assert "confidence" in p, "Missing confidence field"
            assert "last_checked_at" in p, "Missing last_checked_at field"
            # Hardening against fake live data
            if p.get("source") == "mock":
                assert p.get("available") is not False, "Mock data shouldn't have reliable stock"
            if p.get("source") != "mock" and p.get("retailer_slug") == "tesco" and p.get("confidence") == 1.0:
                raise AssertionError("Tesco regex probe should never have 1.0 confidence")

        sources = [p.get("source", "unknown") for p in prices]
        types = [p.get("retailer_slug", "") for p in prices]
        print(f"\n       Veri Kaynakları: {set(sources)}")
        print(f"       Kullanılan Sağlayıcılar: {set(types)}")
        if all("mock" in t or "manual" in t for t in types):
             print("       Not: Sadece mock veya manual veriler dönüyor, canlı market fiyatı YOK.")

    def test_basket():
        payload = {
            "postcode": "SE13",
            "coverage_threshold": 0.8,
            "use_loyalty_prices": False,
            "allow_own_brand": True,
            "items": [
                {"name": "milk", "quantity": 1},
                {"name": "bread", "quantity": 1},
                {"name": "eggs", "quantity": 2},
            ],
        }
        r = httpx.post(f"{BASE}/basket/compare", json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        assert "stores" in data
        assert len(data["stores"]) > 0

    tests = [
        ("GET /health", test_health),
        ("GET /providers/status", test_providers),
        ("GET /products/search?q=milk", test_search),
        ("GET /prices/latest?product=milk", test_prices),
        ("POST /basket/compare", test_basket),
    ]

    for label, fn in tests:
        total += 1
        if check(label, fn):
            passed += 1

    print(f"\n{'=' * 40}")
    print(f"Sonuc: {passed}/{total} test gecti")
    if passed == total:
        print("[PASS] TUM TESTLER GECTI\n")
        return 0
    else:
        print("[FAIL] BAZI TESTLER BASARISIZ\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
