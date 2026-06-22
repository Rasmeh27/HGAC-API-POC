"""Detección de lecturas ambiguas entre candidatos de placa.

Regla (PoC): si dos o más candidatos son válidos, comparten prefijo y longitud,
difieren en exactamente un carácter y sus scores están demasiado cerca, NO se
puede aceptar automáticamente: hay que pedir más evidencia (consenso multi-frame,
más OCR, score muy superior o match contra base autorizada). Nunca se sustituye
un carácter "a mano" (p.ej. G237627 -> G737627).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.modules.lpr.domain.plate_pattern_catalog import plate_prefix

AMBIGUOUS_DIGIT_CONFLICT = "ambiguous_digit_conflict"


@dataclass(frozen=True)
class AmbiguityResult:
    is_ambiguous: bool
    reason: str | None = None
    candidates: tuple[str, str] | None = None


def char_difference(a: str, b: str) -> int:
    """Número de posiciones distintas entre dos cadenas de IGUAL longitud.

    Devuelve un número grande si las longitudes difieren (no comparables por
    sustitución de un carácter).
    """
    if len(a) != len(b):
        return max(len(a), len(b))
    return sum(1 for ca, cb in zip(a, b) if ca != cb)


def detect_ambiguity(
    candidates: Sequence[Mapping[str, object]],
    *,
    min_score_delta: float,
    max_distance: int = 1,
) -> AmbiguityResult:
    """Detecta un conflicto de un carácter entre candidatos válidos con scores cercanos.

    `candidates`: cada uno con `normalized_text`, `score` y `format_valid`.
    `min_score_delta`: si la diferencia de score entre los dos es menor, son ambiguos.
    `max_distance`: distancia de caracteres tolerada (1 = difieren en un carácter).
    """
    # Solo candidatos válidos y distintos; nos quedamos con el mejor score por texto.
    best_by_text: dict[str, float] = {}
    for cand in candidates:
        if not cand.get("format_valid"):
            continue
        text = str(cand.get("normalized_text") or "")
        if not text:
            continue
        score = float(cand.get("score") or 0.0)
        if text not in best_by_text or score > best_by_text[text]:
            best_by_text[text] = score

    items = list(best_by_text.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            text_a, score_a = items[i]
            text_b, score_b = items[j]
            if plate_prefix(text_a) != plate_prefix(text_b):
                continue
            if len(text_a) != len(text_b):
                continue
            distance = char_difference(text_a, text_b)
            if not (1 <= distance <= max_distance):
                continue
            if abs(score_a - score_b) < min_score_delta:
                # El de mayor score primero, para una traza estable.
                pair = (text_a, text_b) if score_a >= score_b else (text_b, text_a)
                return AmbiguityResult(
                    is_ambiguous=True,
                    reason=AMBIGUOUS_DIGIT_CONFLICT,
                    candidates=pair,
                )
    return AmbiguityResult(is_ambiguous=False)
