from __future__ import annotations

from pathlib import Path

import app.db.database as db_module
from app.core.config import get_settings
from app.db.database import SessionLocal, get_engine
from app.db.repositories import WebPriceWatchlistRepository
from app.services.web_price_watchlist_io_service import (
    WATCHLIST_HEADERS,
    export_watchlist_csv_text,
    import_watchlist_csv,
    template_csv_text,
)


def _reset_db(monkeypatch, tmp_path: Path) -> None:
    db_file = tmp_path / "watchlist_io.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    get_settings.cache_clear()
    db_module._engine = None


def test_template_contains_required_headers():
    content = template_csv_text().strip()
    assert content == ",".join(WATCHLIST_HEADERS)


def test_import_rejects_enabled_without_url(monkeypatch, tmp_path):
    _reset_db(monkeypatch, tmp_path)
    csv_path = tmp_path / "watchlist.csv"
    csv_path.write_text(
        "\n".join(
            [
                ",".join(WATCHLIST_HEADERS),
                "tesco,Tesco,milk,,milk,true,24,unconfigured,false,note",
            ]
        ),
        encoding="utf-8",
    )

    report = import_watchlist_csv(csv_path)

    assert report.rows_imported == 0
    assert report.invalid_rows == 1
    assert any("enabled=true requires product_url" in i.message for i in report.validation_issues)


def test_import_rejects_short_frequency_without_flag(monkeypatch, tmp_path):
    _reset_db(monkeypatch, tmp_path)
    csv_path = tmp_path / "watchlist.csv"
    csv_path.write_text(
        "\n".join(
            [
                ",".join(WATCHLIST_HEADERS),
                "tesco,Tesco,milk,https://example.test/milk,milk,true,12,allowed,false,note",
            ]
        ),
        encoding="utf-8",
    )

    report = import_watchlist_csv(csv_path)

    assert report.rows_imported == 0
    assert report.invalid_rows == 1
    assert any("must be >= 24" in i.message for i in report.validation_issues)


def test_import_accepts_short_frequency_with_flag(monkeypatch, tmp_path):
    _reset_db(monkeypatch, tmp_path)
    csv_path = tmp_path / "watchlist.csv"
    csv_path.write_text(
        "\n".join(
            [
                ",".join(WATCHLIST_HEADERS),
                "tesco,Tesco,milk,https://example.test/milk,milk,true,12,allowed,false,note",
            ]
        ),
        encoding="utf-8",
    )

    report = import_watchlist_csv(csv_path, allow_short_frequency=True)

    assert report.rows_imported == 1
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    row = WebPriceWatchlistRepository(db).get_all()[0]
    assert row.max_frequency_hours == 12
    assert row.public_display_allowed is False
    db.close()


def test_import_defaults_public_display_false(monkeypatch, tmp_path):
    _reset_db(monkeypatch, tmp_path)
    csv_path = tmp_path / "watchlist.csv"
    csv_path.write_text(
        "\n".join(
            [
                ",".join(WATCHLIST_HEADERS),
                "tesco,Tesco,milk,https://example.test/milk,milk,false,24,unconfigured,,note",
            ]
        ),
        encoding="utf-8",
    )

    report = import_watchlist_csv(csv_path)

    assert report.rows_imported == 1
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    row = WebPriceWatchlistRepository(db).get_all()[0]
    assert row.public_display_allowed is False
    db.close()


def test_export_returns_rows(monkeypatch, tmp_path):
    _reset_db(monkeypatch, tmp_path)
    csv_path = tmp_path / "watchlist.csv"
    csv_path.write_text(
        "\n".join(
            [
                ",".join(WATCHLIST_HEADERS),
                "tesco,Tesco,milk,https://example.test/milk,milk,false,24,unconfigured,false,note",
            ]
        ),
        encoding="utf-8",
    )
    import_watchlist_csv(csv_path)

    exported = export_watchlist_csv_text()

    assert "retailer_slug,retailer_name,canonical_product_name" in exported
    assert "tesco,Tesco,milk" in exported
