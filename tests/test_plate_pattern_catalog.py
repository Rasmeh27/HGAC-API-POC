"""Tests del catálogo de placas dominicanas y la detección de ambigüedad (puro)."""

from __future__ import annotations

import pytest

from app.modules.lpr.domain.plate_ambiguity import (
    AMBIGUOUS_DIGIT_CONFLICT,
    char_difference,
    detect_ambiguity,
)
from app.modules.lpr.domain.plate_pattern_catalog import DominicanPlatePatternCatalog


@pytest.fixture
def catalog() -> DominicanPlatePatternCatalog:
    return DominicanPlatePatternCatalog()


# code, vehicle_type esperados por placa
@pytest.mark.parametrize(
    "plate,code,vehicle_type",
    [
        ("A123456", "PRIVATE_AUTO", "automovil_privado"),
        ("G123456", "JEEPETA", "jeepeta"),
        ("L123456", "CARGA", "carga"),
        ("F123456", "REMOLQUE", "remolque"),
        ("U123456", "MAQUINA_PESADA", "maquina_pesada"),
        ("J123456", "MONTACARGAS", "montacargas"),
        ("PP123456", "PROVISIONAL_ELECTRONICA", "provisional_electronica"),
        ("EX12345", "EXONERADA", "exonerada"),
        ("DD12345", "DEALER", "dealer"),
        ("OF12345", "OFICIAL", "oficial"),
        ("OP12345", "OFICIAL", "oficial"),
        ("OE12345", "OFICIAL", "oficial"),
        ("OM12345", "OFICIAL", "oficial"),
        ("K1234567", "MOTOCICLETA", "motocicleta"),
    ],
)
def test_classify_known_patterns(catalog, plate, code, vehicle_type) -> None:
    classification = catalog.classify(plate)
    assert classification.is_valid is True
    assert classification.code == code
    assert classification.vehicle_type == vehicle_type
    assert catalog.is_valid(plate) is True


def test_classify_motorcycle_any_leading_letter(catalog) -> None:
    # "una letra + 7 dígitos" para cualquier letra inicial.
    for plate in ("K1234567", "Z0000001", "B9999999"):
        assert catalog.classify(plate).code == "MOTOCICLETA"


def test_prefix_is_computed_from_plate(catalog) -> None:
    assert catalog.classify("A123456").prefix == "A"
    assert catalog.classify("OF12345").prefix == "OF"
    assert catalog.classify("PP123456").prefix == "PP"


@pytest.mark.parametrize(
    "plate",
    ["1234567", "", "ABCDEFG", "A12345", "EX123456", "OF1234", "ZZ12345"],
)
def test_invalid_plates_are_not_valid(catalog, plate) -> None:
    classification = catalog.classify(plate)
    assert classification.is_valid is False
    assert classification.code == "UNKNOWN"
    assert catalog.is_valid(plate) is False


def test_numeric_only_is_not_valid(catalog) -> None:
    # El caso clásico: serial sin letra inicial NO es placa válida.
    assert catalog.is_valid("1234567") is False
    assert catalog.is_valid("460432") is False


def test_get_expected_patterns_lists_codes(catalog) -> None:
    patterns = catalog.get_expected_patterns()
    assert isinstance(patterns, list)
    assert all(isinstance(p, str) for p in patterns)
    joined = " ".join(patterns)
    assert "PRIVATE_AUTO" in joined and "MOTOCICLETA" in joined


# ---- ambigüedad ----


def test_char_difference() -> None:
    assert char_difference("G237627", "G737627") == 1
    assert char_difference("G237627", "G237627") == 0
    assert char_difference("G237627", "G738627") == 2
    assert char_difference("ABC", "ABCD") == 4  # longitudes distintas -> grande


def _cand(text: str, score: float, valid: bool = True) -> dict:
    return {"normalized_text": text, "score": score, "format_valid": valid}


def test_g237627_vs_g737627_is_ambiguous_when_scores_close() -> None:
    result = detect_ambiguity(
        [_cand("G237627", 80.0), _cand("G737627", 78.0)],
        min_score_delta=15.0,
        max_distance=1,
    )
    assert result.is_ambiguous is True
    assert result.reason == AMBIGUOUS_DIGIT_CONFLICT
    assert set(result.candidates) == {"G237627", "G737627"}


def test_not_ambiguous_when_score_delta_is_strong() -> None:
    result = detect_ambiguity(
        [_cand("G237627", 90.0), _cand("G737627", 60.0)],
        min_score_delta=15.0,
        max_distance=1,
    )
    assert result.is_ambiguous is False


def test_not_ambiguous_when_different_prefix() -> None:
    result = detect_ambiguity(
        [_cand("A237627", 80.0), _cand("G237627", 79.0)],
        min_score_delta=15.0,
        max_distance=1,
    )
    assert result.is_ambiguous is False


def test_not_ambiguous_when_more_than_one_char_differs() -> None:
    result = detect_ambiguity(
        [_cand("G237627", 80.0), _cand("G738627", 79.0)],
        min_score_delta=15.0,
        max_distance=1,
    )
    assert result.is_ambiguous is False


def test_invalid_candidates_are_ignored_for_ambiguity() -> None:
    result = detect_ambiguity(
        [_cand("1237627", 80.0, valid=False), _cand("1737627", 79.0, valid=False)],
        min_score_delta=15.0,
        max_distance=1,
    )
    assert result.is_ambiguous is False
