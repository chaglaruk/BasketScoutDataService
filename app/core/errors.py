"""Uygulama genelinde hata tipleri ve HTTP hata yardımcıları."""

from __future__ import annotations

from fastapi import HTTPException, status


class BasketScoutError(Exception):
    """Temel uygulama hatası."""


class ProviderError(BasketScoutError):
    """Provider'dan veri alınırken oluşan hata."""

    def __init__(self, provider_name: str, message: str) -> None:
        self.provider_name = provider_name
        super().__init__(f"[{provider_name}] {message}")


class ProductNotFoundError(BasketScoutError):
    """Ürün bulunamadı."""


class CacheExpiredError(BasketScoutError):
    """Cache süresi dolmuş."""


def not_found(detail: str = "Bulunamadı") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def service_unavailable(detail: str = "Servis geçici olarak kullanılamıyor") -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
