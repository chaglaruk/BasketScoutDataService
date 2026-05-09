"""Sepet optimizasyonu — en ucuz perakendeci karşılaştırması."""

from __future__ import annotations

from app.core.time import utcnow
from app.domain.models import (
    BasketCompareMetadata,
    BasketCompareRecommended,
    BasketCompareRequest,
    BasketCompareResponse,
    BasketLineItem,
    PriceItem,
    StoreBasketResult,
)
from app.domain.normalization import normalize_name


def compare_basket(
    request: BasketCompareRequest,
    price_data: dict[str, list[PriceItem]],  # retailer_slug -> PriceItem listesi
    data_mode: str = "mock",
    warnings: list[str] | None = None,
) -> BasketCompareResponse:
    """
    Sepet karşılaştırması yapar.

    Sıralama:
    1. Kapsama eşiğini karşılayanlar önce
    2. Toplam fiyat artan
    3. Kapsama oranı azalan
    4. Perakendeci adı artan
    """
    if warnings is None:
        warnings = []

    requested_count = len(request.items)
    store_results: list[StoreBasketResult] = []

    for retailer_slug, prices in price_data.items():
        if not prices:
            continue

        retailer_name = prices[0].retailer if prices else retailer_slug
        line_items: list[BasketLineItem] = []
        total_price = 0.0
        matched_count = 0
        missing_items: list[str] = []

        for item in request.items:
            best_match: PriceItem | None = None
            best_score = 0.0

            for p in prices:
                if not request.allow_own_brand and p.own_brand:
                    continue
                score = _match_score(item.name, p.product)
                if score > best_score:
                    best_score = score
                    best_match = p

            if best_match and best_score >= 0.3:
                effective_price = (
                    best_match.loyalty_price
                    if (request.use_loyalty_prices and best_match.loyalty_price is not None)
                    else best_match.price
                )
                line_total = effective_price * item.quantity
                total_price += line_total
                matched_count += 1
                line_items.append(
                    BasketLineItem(
                        requested_name=item.name,
                        canonical_name=best_match.product,
                        quantity=item.quantity,
                        unit_price=effective_price,
                        line_total=line_total,
                        available=best_match.available,
                        source=best_match.source,
                        source_url=best_match.source_url,
                        last_checked_at=best_match.last_checked_at,
                        confidence=best_match.confidence,
                        is_stale=best_match.is_stale,
                    )
                )
            else:
                missing_items.append(item.name)
                line_items.append(
                    BasketLineItem(
                        requested_name=item.name,
                        canonical_name=None,
                        quantity=item.quantity,
                    )
                )

        coverage = matched_count / requested_count if requested_count > 0 else 0.0
        qualifies = coverage >= request.coverage_threshold

        store_results.append(
            StoreBasketResult(
                retailer=retailer_name,
                retailer_slug=retailer_slug,
                qualifies=qualifies,
                total_price=round(total_price, 2),
                coverage=round(coverage, 4),
                matched_count=matched_count,
                missing_items=missing_items,
                line_items=line_items,
            )
        )

    # Sıralama
    store_results.sort(
        key=lambda s: (
            0 if s.qualifies else 1,
            s.total_price,
            -s.coverage,
            s.retailer,
        )
    )

    recommended: BasketCompareRecommended | None = None
    qualifying = [s for s in store_results if s.qualifies]

    if qualifying:
        best = qualifying[0]
        priciest_price = max((s.total_price for s in qualifying), default=best.total_price)
        recommended = BasketCompareRecommended(
            retailer=best.retailer,
            total_price=best.total_price,
            coverage=best.coverage,
            matched_count=best.matched_count,
            requested_count=requested_count,
            missing_items=best.missing_items,
            savings_vs_priciest=round(priciest_price - best.total_price, 2),
        )
    else:
        warnings.append(
            "Hiçbir mağaza kapsama eşiğini karşılamadı. En yakın sonuçlar gösteriliyor."
        )

    return BasketCompareResponse(
        recommended=recommended,
        stores=store_results,
        metadata=BasketCompareMetadata(
            data_mode=data_mode,
            generated_at=utcnow(),
            warnings=warnings,
        ),
    )


def _match_score(query: str, candidate: str) -> float:
    from app.domain.normalization import similarity_score

    return similarity_score(normalize_name(query), normalize_name(candidate))
