"""RefreshService — provider'ları manuel veya zamanlanmış olarak yeniler."""

from __future__ import annotations

import logging

from app.services.provider_registry import get_registry

logger = logging.getLogger(__name__)


class RefreshService:
    def refresh_all(self, product_names: list[str] | None = None) -> list[dict]:
        """Tüm aktif provider'ları yeniler."""
        registry = get_registry()
        results: list[dict] = []
        for p in registry.all():
            try:
                result = p.refresh_products(product_names=product_names)
                results.append(result)
            except Exception as exc:
                logger.error(f"[{p.name}] refresh hatası: {exc}")
                results.append(
                    {
                        "provider": p.name,
                        "status": "error",
                        "message": str(exc),
                    }
                )
        return results

    def refresh_provider(self, name: str, product_names: list[str] | None = None) -> dict:
        """Belirtilen provider'ı yeniler."""
        registry = get_registry()
        p = registry.get(name)
        if p is None:
            return {"provider": name, "status": "not_found"}
        try:
            return p.refresh_products(product_names=product_names)
        except Exception as exc:
            logger.error(f"[{name}] refresh hatası: {exc}")
            return {"provider": name, "status": "error", "message": str(exc)}
