from app.core.config import Settings


def test_debug_env_accepts_release_alias(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG", "release")
    settings = Settings()
    assert settings.debug is False


def test_debug_env_accepts_development_alias(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG", "development")
    settings = Settings()
    assert settings.debug is True


def test_host_port_aliases_supported(monkeypatch) -> None:
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9999")
    settings = Settings()
    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 9999


def test_sqlite_path_builds_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SQLITE_PATH", "./data/prod.db")
    settings = Settings()
    assert settings.database_url == "sqlite:///./data/prod.db"


def test_cors_origins_parse_csv(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://a.example, https://b.example")
    settings = Settings()
    assert settings.cors_allowed_origins_list == ["https://a.example", "https://b.example"]
