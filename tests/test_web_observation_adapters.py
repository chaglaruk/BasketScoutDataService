from __future__ import annotations

from app.providers.web_observation_adapters import (
    OUTCOME_BLOCKED_ACCESS,
    OUTCOME_PARSE_FAILED,
    OUTCOME_SUCCESS,
    TescoWebObservationAdapter,
)


class _FakeResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, *args, **kwargs):
        return self._response


def test_403_maps_to_blocked_access(monkeypatch):
    monkeypatch.setattr(
        "app.providers.web_observation_adapters.httpx.Client",
        lambda *args, **kwargs: _FakeClient(_FakeResponse(403, "forbidden")),
    )
    adapter = TescoWebObservationAdapter(timeout_seconds=5, user_agent="test-agent")
    result = adapter.observe(
        product_url="https://example.test/milk",
        expected_keywords=["milk"],
        canonical_product_name="Semi-Skimmed Milk 2L",
        dry_run=False,
    )
    assert result.status == OUTCOME_BLOCKED_ACCESS


def test_captcha_marker_maps_to_blocked_access(monkeypatch):
    monkeypatch.setattr(
        "app.providers.web_observation_adapters.httpx.Client",
        lambda *args, **kwargs: _FakeClient(_FakeResponse(200, "Please solve captcha")),
    )
    adapter = TescoWebObservationAdapter(timeout_seconds=5, user_agent="test-agent")
    result = adapter.observe(
        product_url="https://example.test/milk",
        expected_keywords=["milk"],
        canonical_product_name="Semi-Skimmed Milk 2L",
        dry_run=False,
    )
    assert result.status == OUTCOME_BLOCKED_ACCESS


def test_missing_price_maps_to_parse_failed(monkeypatch):
    monkeypatch.setattr(
        "app.providers.web_observation_adapters.httpx.Client",
        lambda *args, **kwargs: _FakeClient(_FakeResponse(200, "<title>Milk page</title> no prices here")),
    )
    adapter = TescoWebObservationAdapter(timeout_seconds=5, user_agent="test-agent")
    result = adapter.observe(
        product_url="https://example.test/milk",
        expected_keywords=["milk"],
        canonical_product_name="Semi-Skimmed Milk 2L",
        dry_run=False,
    )
    assert result.status == OUTCOME_PARSE_FAILED


def test_price_pattern_maps_to_success(monkeypatch):
    html = "<title>Tesco Milk 2L</title><div>Clubcard Price GBP 1.45</div>"
    monkeypatch.setattr(
        "app.providers.web_observation_adapters.httpx.Client",
        lambda *args, **kwargs: _FakeClient(_FakeResponse(200, html)),
    )
    adapter = TescoWebObservationAdapter(timeout_seconds=5, user_agent="test-agent")
    result = adapter.observe(
        product_url="https://example.test/milk",
        expected_keywords=["milk"],
        canonical_product_name="Semi-Skimmed Milk 2L",
        dry_run=False,
    )
    assert result.status == OUTCOME_SUCCESS
    assert result.price_amount is not None
