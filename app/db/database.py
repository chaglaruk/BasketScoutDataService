"""SQLAlchemy veritabanı bağlantısı ve session yönetimi."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


def _get_engine():
    settings = get_settings()
    db_url = settings.database_url

    # SQLite için veri dizinini oluştur
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path and not db_path.startswith(":"):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
    )

    # SQLite WAL modu — eşzamanlı okuma için
    if db_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def set_wal(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _get_engine()
    return _engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=None)


def get_session() -> Session:
    """Bağımlılık enjeksiyonu için veritabanı session'ı döndürür."""
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Veritabanı tablolarını oluşturur."""
    from app.db import models  # noqa: F401 — modelleri kaydet

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
