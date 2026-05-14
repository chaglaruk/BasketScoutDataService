from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import app.db.database as db_module
import app.services.provider_registry as registry_module
from app.core.config import get_settings
from app.core.time import utcnow
from app.db.database import SessionLocal, get_engine, init_db
from app.db.models import PriceObservation
from app.db.repositories import ProviderRunRepository, WebPriceWatchlistRepository
from app.db.seed import seed_all
from app.domain.models import BasketCompareRequest, BasketItem
from app.providers.web_observation_adapters import (
    OUTCOME_BLOCKED_ACCESS,
    OUTCOME_PARSE_FAILED,
    OUTCOME_SUCCESS,
    AdapterObservationResult,
)
from app.providers.web_observation_provider import WebObservationProvider
from app.services import web_price_observation_service as obs_service
from app.services.basket_service import BasketService


def _reset_test_db(monkeypatch, tmp_path: Path) -> None:
    db_file = tmp_path / "obs_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("ENV", "development")
    get_settings.cache_clear()
    db_module._engine = None
    registry_module._registry = None
    init_db()
    seed_all()


class _FakeAdapter:
    def __init__(self, result: AdapterObservationResult) -> None:
        self._result = result

    def observe(self, **kwargs):  # noqa: ANN003
        return self._result


def test_disabled_watchlist_rows_are_skipped(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    report = obs_service.run_daily_price_observation(dry_run=True)

    assert report.urls_attempted == 0
    assert report.prices_observed == 0
    assert report.warnings


def test_max_frequency_blocks_repeat_fetch(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    row = repo.upsert(
        retailer_slug="tesco",
        retailer_name="Tesco",
        canonical_product_name="Semi-Skimmed Milk 2L",
        product_url="https://example.test/milk",
        expected_product_keywords="milk",
        enabled=True,
        policy_status="allowed",
    )
    row.last_attempt_at = utcnow()
    db.commit()
    db.close()

    monkeypatch.setattr(obs_service, "_check_policy_and_robots", lambda *a, **k: (True, "allowed"))
    monkeypatch.setattr(
        obs_service,
        "_adapter_for_slug",
        lambda *a, **k: _FakeAdapter(
            AdapterObservationResult(
                status=OUTCOME_SUCCESS,
                observed_at=utcnow(),
                captured_at=utcnow(),
                price_amount=1.23,
                parser_confidence=0.8,
            )
        ),
    )

    report = obs_service.run_daily_price_observation(dry_run=True, force=False)

    assert report.urls_attempted == 0
    assert any("max_frequency_hours" in w for w in report.warnings)


def test_access_control_block_is_recorded(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    row = repo.upsert(
        retailer_slug="tesco",
        retailer_name="Tesco",
        canonical_product_name="Semi-Skimmed Milk 2L",
        product_url="https://example.test/milk",
        expected_product_keywords="milk",
        enabled=True,
        policy_status="allowed",
    )
    row.last_attempt_at = utcnow() - timedelta(hours=48)
    db.commit()
    db.close()

    monkeypatch.setattr(obs_service, "_check_policy_and_robots", lambda *a, **k: (True, "allowed"))
    monkeypatch.setattr(
        obs_service,
        "_adapter_for_slug",
        lambda *a, **k: _FakeAdapter(
            AdapterObservationResult(
                status=OUTCOME_BLOCKED_ACCESS,
                observed_at=utcnow(),
                captured_at=utcnow(),
                error_message="HTTP 403",
            )
        ),
    )

    report = obs_service.run_daily_price_observation(dry_run=False, force=True)

    assert report.urls_attempted == 1
    assert report.blocked_by_access == 1


def test_policy_block_is_recorded(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    repo.upsert(
        retailer_slug="aldi",
        retailer_name="Aldi",
        canonical_product_name="White Bread 800g",
        product_url="https://example.test/bread",
        expected_product_keywords="bread",
        enabled=True,
        policy_status="allowed",
    )
    db.commit()
    db.close()

    monkeypatch.setattr(
        obs_service,
        "_check_policy_and_robots",
        lambda *a, **k: (False, "robots disallow"),
    )

    report = obs_service.run_daily_price_observation(dry_run=True, force=True)

    assert report.urls_attempted == 0
    assert report.blocked_by_policy == 1


def test_parse_failure_is_recorded(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    repo.upsert(
        retailer_slug="lidl",
        retailer_name="Lidl",
        canonical_product_name="White Bread 800g",
        product_url="https://example.test/bread",
        expected_product_keywords="bread",
        enabled=True,
        policy_status="allowed",
    )
    db.commit()
    db.close()

    monkeypatch.setattr(obs_service, "_check_policy_and_robots", lambda *a, **k: (True, "allowed"))
    monkeypatch.setattr(
        obs_service,
        "_adapter_for_slug",
        lambda *a, **k: _FakeAdapter(
            AdapterObservationResult(
                status=OUTCOME_PARSE_FAILED,
                observed_at=utcnow(),
                captured_at=utcnow(),
                error_message="No GBP pattern",
            )
        ),
    )

    report = obs_service.run_daily_price_observation(dry_run=False, force=True)

    assert report.parse_failed == 1


def test_success_observation_stock_unknown_and_internal_only_hidden(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    repo.upsert(
        retailer_slug="tesco",
        retailer_name="Tesco",
        canonical_product_name="Semi-Skimmed Milk 2L",
        product_url="https://example.test/milk",
        expected_product_keywords="milk",
        enabled=True,
        policy_status="allowed",
        public_display_allowed=False,
    )
    db.commit()
    db.close()

    monkeypatch.setattr(obs_service, "_check_policy_and_robots", lambda *a, **k: (True, "allowed"))
    monkeypatch.setattr(
        obs_service,
        "_adapter_for_slug",
        lambda *a, **k: _FakeAdapter(
            AdapterObservationResult(
                status=OUTCOME_SUCCESS,
                observed_at=utcnow(),
                captured_at=utcnow(),
                raw_product_name="Milk product",
                price_amount=1.50,
                parser_confidence=0.75,
            )
        ),
    )

    report = obs_service.run_daily_price_observation(dry_run=False, force=True)
    assert report.prices_observed == 1
    assert report.observations_internal_only == 1
    assert report.observations_published == 0

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    obs_row = db.query(PriceObservation).first()
    assert obs_row is not None
    assert obs_row.stock_status == "Unknown"
    db.close()

    provider = WebObservationProvider()
    prices = provider.get_latest_prices(["Semi-Skimmed Milk 2L"])
    assert prices == []


def test_provider_run_summary_and_report_fields(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    repo = WebPriceWatchlistRepository(db)
    repo.upsert(
        retailer_slug="tesco",
        retailer_name="Tesco",
        canonical_product_name="Semi-Skimmed Milk 2L",
        product_url="https://example.test/milk",
        expected_product_keywords="milk",
        enabled=True,
        policy_status="allowed",
        public_display_allowed=True,
    )
    db.commit()
    db.close()

    monkeypatch.setattr(obs_service, "_check_policy_and_robots", lambda *a, **k: (True, "allowed"))
    monkeypatch.setattr(
        obs_service,
        "_adapter_for_slug",
        lambda *a, **k: _FakeAdapter(
            AdapterObservationResult(
                status=OUTCOME_SUCCESS,
                observed_at=utcnow(),
                captured_at=utcnow(),
                raw_product_name="Milk",
                price_amount=1.42,
                parser_confidence=0.78,
            )
        ),
    )

    report = obs_service.run_daily_price_observation(dry_run=False, force=True)

    assert report.started_at
    assert report.finished_at
    assert report.retailers_attempted >= 1
    assert report.urls_attempted == 1
    assert report.prices_observed == 1

    report_path = Path("artifacts/latest-price-observation-report.json")
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    required = {
        "started_at",
        "finished_at",
        "retailers_attempted",
        "urls_attempted",
        "prices_observed",
        "blocked_by_policy",
        "blocked_by_access",
        "parse_failed",
        "network_failed",
        "observations_published",
        "observations_internal_only",
        "warnings",
        "errors",
    }
    assert required.issubset(payload.keys())

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    run = ProviderRunRepository(db).get_last_for_provider("daily_web_observation")
    assert run is not None
    assert run.status in {"success", "partial"}
    message_payload = json.loads(run.message or "{}")
    assert "prices_observed" in message_payload
    assert "report_path" in message_payload
    db.close()


def test_public_observation_can_be_used_and_has_warning(monkeypatch, tmp_path):
    _reset_test_db(monkeypatch, tmp_path)

    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    watch = WebPriceWatchlistRepository(db).upsert(
        retailer_slug="tesco",
        retailer_name="Tesco",
        canonical_product_name="Tracked Test Product",
        product_url="https://example.test/product",
        expected_product_keywords="tracked,test",
        enabled=True,
        policy_status="allowed",
        public_display_allowed=True,
    )
    obs = PriceObservation(
        watchlist_id=watch.id,
        run_id=None,
        retailer_slug="tesco",
        retailer_name="Tesco",
        canonical_product_name="Tracked Test Product",
        raw_product_name="Tracked Test Product Tesco",
        price_amount=2.99,
        currency="GBP",
        loyalty_price_amount=None,
        observed_at=utcnow(),
        captured_at=utcnow(),
        provider_used="web_observation_tesco",
        data_mode="observed_web_price",
        confidence_score=0.72,
        freshness_bucket="fresh_24h",
        source_url="https://example.test/product",
        stock_status="Unknown",
        warnings=None,
        parser_confidence=0.72,
        public_display_allowed=True,
        rights_status="public_allowed",
        raw_snippet_hash="abc",
        outcome_status="SUCCESS",
        error_type=None,
        error_message=None,
    )
    db.add(obs)
    db.commit()
    db.close()

    provider = WebObservationProvider()
    prices = provider.get_latest_prices(["Tracked Test Product"])
    assert len(prices) == 1
    assert prices[0].source == "Observed web price"
    assert prices[0].available is None

    service = BasketService()
    response = service.compare(
        BasketCompareRequest(
            items=[BasketItem(name="Tracked Test Product", quantity=1)],
            coverage_threshold=0.0,
            use_loyalty_prices=False,
            allow_own_brand=True,
        )
    )
    assert any("Observed from public web page. Price may change." in w for w in response.metadata.warnings)
