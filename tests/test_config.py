from app.core.config import Settings


def test_debug_env_accepts_release_alias(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG", "release")
    settings = Settings()
    assert settings.debug is False


def test_debug_env_accepts_development_alias(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG", "development")
    settings = Settings()
    assert settings.debug is True
