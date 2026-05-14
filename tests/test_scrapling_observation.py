from __future__ import annotations

from pathlib import Path

import pytest

import app.db.database as db_module
import app.services.provider_registry as registry_module
from app.core.config import get_settings
from app.db.database import SessionLocal, get_engine, init_db
from app.db.models import PriceObservation
from app.db.repositories import WebPriceWatchlistRepository
from app.db.seed import seed_all
from app.providers.web_observation_adapters import (
    OUTCOME_BLOCKED_ACCESS,
    OUTCOME_PARSE_FAILED,
    OUTCOME_SUCCESS,
)
from app.services import scrapling_price_observation_service as scrap_service

pytest.importorskip("scrapling")

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "scrapling"


def _fixture_text(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _reset_test_db(monkeypatch, tmp_path: Path) -> None:
    db_file = tmp_path / "scrapling_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("SCRAPLING_ENABLED", "true")
    monkeypatch.setenv("SCRAPLING_NETWORK_ENABLED", "true")
    get_settings.cache_clear()
    db_module._engine = None
    registry_module._registry = None
    init_db()
    seed_all()


@pytest.mark.parametrize(
    ("fixture_name", "expected_price"),
    [
        ("tesco_price_sample.html", 1.65),
        ("aldi_price_sample.html", 1.49),
        ("sainsburys_price_sample.html", 1.85),
        ("lidl_price_sample.html", 1.25),
    ],
)
def test_scrapling_parser_extracts_price_from_fixture(fixture_name: str, expected_price: float):
    result = scrap_service.parse_html_with_scrapling(
        page_html=_fixture_text(fixture_name),
        source_url="https://example.test/product",
        expected_keywords=["milk"],
        canonical_product_name="milk",
    )
    assert result.status == OUTCOME_SUCCESS
    assert result.price_amount == expected_price


def test_scrapling_parser_marks_blocked_access_fixture():
    result = scrap_service.parse_html_with_scrapling(
        page_html=_fixture_text("blocked_access_sample.html"),
        source_url="https://example.test/blocked",
        expected_keywords=["milk"],
        canonical_product_name="milk",
    )
    assert result.status == OUTCOME_BLOCKED_ACCESS


def test_scrapling_parser_rejects_no_price_fixture():
    result = scrap_service.parse_html_with_scrapling(
        page_html=_fixture_text("no_price_sample.html"),
        source_url="https://example.test/no-price",
        expected_keywords=["milk"],
        canonical_product_name="milk",
    )
    assert result.status == OUTCOME_PARSE_FAILED


def test_scrapling_observation_low_confidence_stays_internal(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    repo.upsert(
        retailer_slug="tesco",
        retailer_name="Tesco",
        canonical_product_name="milk",
        product_url="https://example.test/milk",
        expected_product_keywords="nonmatching-keyword",
        enabled=True,
        policy_status="allowed",
        public_display_allowed=True,
    )
    db.commit()
    db.close()

    monkeypatch.setattr(scrap_service, "_check_policy_and_robots", lambda *a, **k: (True, "allowed"))

    class _Resp:
        status_code = 200
        text = _fixture_text("tesco_price_sample.html")

    monkeypatch.setattr(scrap_service.httpx, "get", lambda *a, **k: _Resp())

    report = scrap_service.run_scrapling_price_observation(dry_run=False, force=True)
    assert report.urls_attempted == 1
    assert report.prices_observed == 1
    assert report.observations_published == 0
    assert report.observations_internal_only == 1

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    row = db.query(PriceObservation).first()
    assert row is not None
    assert row.stock_status == "Unknown"
    assert row.public_display_allowed is False
    assert row.rights_status == "internal_review_required"
    db.close()

