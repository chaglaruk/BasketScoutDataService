"""test_normalization.py — İsim normalleştirme birimi testleri."""
from __future__ import annotations

from app.domain.normalization import is_match, normalize_name, similarity_score, tokenize


def test_normalize_lowercase():
    assert normalize_name("MILK") == "milk"


def test_normalize_strips_punctuation():
    result = normalize_name("bread & butter!")
    assert "&" not in result
    assert "!" not in result


def test_normalize_unicode():
    assert normalize_name("café") == "cafe"


def test_normalize_unit_alias():
    assert "l" in normalize_name("2 litres milk")


def test_similarity_exact():
    assert similarity_score("milk", "milk") == 1.0


def test_similarity_partial():
    score = similarity_score("semi skimmed milk", "milk")
    assert 0.0 < score < 1.0


def test_similarity_no_overlap():
    assert similarity_score("milk", "bread") == 0.0


def test_is_match_true():
    assert is_match("milk", "semi skimmed milk", threshold=0.3)


def test_is_match_false():
    assert not is_match("milk", "bread butter jam", threshold=0.5)


def test_tokenize_removes_stopwords():
    tokens = tokenize("a carton of milk")
    assert "a" not in tokens
    assert "of" not in tokens
    assert "milk" in tokens


def test_normalize_whitespace():
    assert normalize_name("  milk   ") == "milk"
