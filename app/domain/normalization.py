"""İsim normalleştirme yardımcıları."""

from __future__ import annotations

import re
import unicodedata

_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "of",
        "with",
        "and",
        "in",
        "for",
        "or",
        "to",
        "at",
        "by",
        "from",
        "on",
    }
)

_UNIT_ALIASES: dict[str, str] = {
    "litre": "l",
    "litres": "l",
    "liter": "l",
    "liters": "l",
    "millilitre": "ml",
    "millilitres": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "kilogram": "kg",
    "kilograms": "kg",
    "gram": "g",
    "grams": "g",
    "ounce": "oz",
    "ounces": "oz",
    "pound": "lb",
    "pounds": "lb",
    "pint": "pt",
    "pints": "pt",
}


def normalize_name(text: str) -> str:
    """
    Ürün ismini normalleştirir:
    - Küçük harfe çevirir
    - Unicode aksan karakterlerini temizler
    - Özel karakterleri kaldırır
    - Gereksiz boşlukları siler
    """
    text = text.strip().lower()
    # Unicode normalleştirme (é -> e)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Alfanümerik ve boşluklar dışındakileri kaldır
    text = re.sub(r"[^\w\s]", " ", text)
    # Birden fazla boşluğu teke indir
    text = re.sub(r"\s+", " ", text).strip()
    # Birim takma adlarını genişlet
    words = text.split()
    words = [_UNIT_ALIASES.get(w, w) for w in words]
    return " ".join(words)


def tokenize(text: str) -> list[str]:
    """İsmi tokenize eder, stop word'leri çıkarır."""
    words = normalize_name(text).split()
    return [w for w in words if w not in _STOPWORDS]


def similarity_score(a: str, b: str) -> float:
    """
    İki normalize edilmiş isim arasında basit token örtüşme skoru döndürür.
    0.0 (hiç örtüşme yok) — 1.0 (tam eşleşme).
    """
    ta = set(tokenize(a))
    tb = set(tokenize(b))
    if not ta or not tb:
        return 0.0
    intersection = ta & tb
    union = ta | tb
    return len(intersection) / len(union)


def is_match(query: str, candidate: str, threshold: float = 0.5) -> bool:
    """Verilen eşik değerinde iki ismin eşleşip eşleşmediğini döndürür."""
    return similarity_score(normalize_name(query), normalize_name(candidate)) >= threshold
