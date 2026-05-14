"""Safe web observation adapters for tracked product URLs only."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx

logger = logging.getLogger(__name__)

OUTCOME_SUCCESS = "SUCCESS"
OUTCOME_BLOCKED_ACCESS = "BLOCKED_BY_ACCESS_CONTROL"
OUTCOME_PARSE_FAILED = "PARSE_FAILED"
OUTCOME_NETWORK_FAILED = "NETWORK_FAILED"
OUTCOME_DRY_RUN = "DRY_RUN_SKIPPED"

_BLOCK_PATTERNS = (
    "captcha",
    "access denied",
    "forbidden",
    "unusual traffic",
    "verify you are human",
    "bot",
    "challenge",
    "cloudflare",
)

_PRICE_PATTERNS = (
    re.compile(r"(?:\u00a3|gbp\s?)(\d{1,3}(?:\.\d{1,2})?)", re.IGNORECASE),
    re.compile(r"(\d{1,3}(?:\.\d{1,2})?)\s?(?:\u00a3|gbp)", re.IGNORECASE),
)

_TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


@dataclass
class AdapterObservationResult:
    status: str
    observed_at: datetime
    captured_at: datetime
    raw_product_name: str | None = None
    price_amount: float | None = None
    loyalty_price_amount: float | None = None
    parser_confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    raw_snippet_hash: str | None = None
    error_message: str | None = None


class BaseWebObservationAdapter:
    retailer_slug: str = "unknown"
    retailer_name: str = "Unknown"

    def __init__(self, timeout_seconds: float, user_agent: str) -> None:
        self._timeout = timeout_seconds
        self._user_agent = user_agent

    def observe(
        self,
        *,
        product_url: str,
        expected_keywords: list[str],
        canonical_product_name: str,
        dry_run: bool = False,
    ) -> AdapterObservationResult:
        now = datetime.now(UTC)
        if dry_run:
            return AdapterObservationResult(
                status=OUTCOME_DRY_RUN,
                observed_at=now,
                captured_at=now,
                warnings=["Dry-run mode: no network call was made."],
                error_message="DRY_RUN",
            )

        headers = {
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
                response = client.get(product_url, headers=headers)
        except Exception as exc:  # noqa: BLE001
            logger.warning("%s observation network failure: %s", self.retailer_slug, exc)
            return AdapterObservationResult(
                status=OUTCOME_NETWORK_FAILED,
                observed_at=now,
                captured_at=now,
                error_message=str(exc),
            )

        body = response.text or ""
        body_lower = body.lower()

        if response.status_code in {401, 403, 429}:
            return AdapterObservationResult(
                status=OUTCOME_BLOCKED_ACCESS,
                observed_at=now,
                captured_at=now,
                error_message=f"HTTP {response.status_code}",
            )

        if any(marker in body_lower for marker in _BLOCK_PATTERNS):
            return AdapterObservationResult(
                status=OUTCOME_BLOCKED_ACCESS,
                observed_at=now,
                captured_at=now,
                error_message="Access-control marker detected in page content.",
            )

        if response.status_code >= 400:
            return AdapterObservationResult(
                status=OUTCOME_NETWORK_FAILED,
                observed_at=now,
                captured_at=now,
                error_message=f"HTTP {response.status_code}",
            )

        return self._parse_observation(
            page_html=body,
            expected_keywords=expected_keywords,
            canonical_product_name=canonical_product_name,
            observed_at=now,
        )

    def _parse_observation(
        self,
        *,
        page_html: str,
        expected_keywords: list[str],
        canonical_product_name: str,
        observed_at: datetime,
    ) -> AdapterObservationResult:
        title_match = _TITLE_PATTERN.search(page_html)
        raw_product_name = None
        if title_match:
            raw_product_name = re.sub(r"\s+", " ", title_match.group(1)).strip()

        page_lower = page_html.lower()
        keywords = [kw.strip().lower() for kw in expected_keywords if kw.strip()]
        keyword_hits = sum(1 for keyword in keywords if keyword in page_lower)

        snippet = page_html[:2000]
        snippet_hash = hashlib.sha256(snippet.encode("utf-8", errors="ignore")).hexdigest()

        found_prices: list[float] = []
        for pattern in _PRICE_PATTERNS:
            for match in pattern.findall(page_html):
                try:
                    found_prices.append(float(match))
                except ValueError:
                    continue

        if not found_prices:
            return AdapterObservationResult(
                status=OUTCOME_PARSE_FAILED,
                observed_at=observed_at,
                captured_at=observed_at,
                raw_product_name=raw_product_name,
                parser_confidence=0.0,
                raw_snippet_hash=snippet_hash,
                error_message="No GBP price pattern found.",
            )

        warnings: list[str] = []
        if keywords and keyword_hits == 0:
            warnings.append("Expected product keywords were not found in page text.")

        parser_confidence = 0.55
        if keywords and keyword_hits > 0:
            parser_confidence = 0.7
        elif not keywords and canonical_product_name.lower() in page_lower:
            parser_confidence = 0.65

        loyalty_price = None
        if (
            "clubcard" in page_lower or "nectar" in page_lower or "lidl plus" in page_lower
        ) and len(found_prices) >= 2:
            loyalty_price = min(found_prices)

        return AdapterObservationResult(
            status=OUTCOME_SUCCESS,
            observed_at=observed_at,
            captured_at=observed_at,
            raw_product_name=raw_product_name,
            price_amount=found_prices[0],
            loyalty_price_amount=loyalty_price,
            parser_confidence=parser_confidence,
            warnings=warnings,
            raw_snippet_hash=snippet_hash,
        )


class TescoWebObservationAdapter(BaseWebObservationAdapter):
    retailer_slug = "tesco"
    retailer_name = "Tesco"


class AldiWebObservationAdapter(BaseWebObservationAdapter):
    retailer_slug = "aldi"
    retailer_name = "Aldi"


class SainsburyWebObservationAdapter(BaseWebObservationAdapter):
    retailer_slug = "sainsburys"
    retailer_name = "Sainsbury's"


class LidlWebObservationAdapter(BaseWebObservationAdapter):
    retailer_slug = "lidl"
    retailer_name = "Lidl"
