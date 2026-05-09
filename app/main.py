"""FastAPI uygulama giriş noktası."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_admin,
    routes_basket,
    routes_health,
    routes_prices,
    routes_products,
    routes_providers,
)
from app.core.config import get_settings
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatma ve kapatma yaşam döngüsü."""
    setup_logging()
    settings = get_settings()
    logger.info(
        f"BasketScoutDataService başlatılıyor — v{settings.app_version} / {settings.app_env}"
    )
    # Veritabanını başlat
    try:
        from app.db.database import init_db

        init_db()
        logger.info("Veritabanı başlatıldı.")
    except Exception as exc:
        logger.error(f"Veritabanı başlatma hatası: {exc}")

    # Provider registry başlat
    try:
        from app.services.provider_registry import get_registry

        registry = get_registry()
        logger.info(f"Provider registry hazır — {len(registry.all())} provider.")
    except Exception as exc:
        logger.error(f"Provider registry başlatma hatası: {exc}")

    yield

    logger.info("BasketScoutDataService durduruluyor.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="BasketScoutDataService",
        description=(
            "BasketScout Android uygulaması için self-hosted backend veri servisi. "
            "Bakkal ürün fiyatlarını toplar, normalize eder ve karşılaştırır."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — Android uygulaması için
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Router'ları ekle
    app.include_router(routes_health.router)
    app.include_router(routes_providers.router)
    app.include_router(routes_products.router)
    app.include_router(routes_prices.router)
    app.include_router(routes_basket.router)
    app.include_router(routes_admin.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
