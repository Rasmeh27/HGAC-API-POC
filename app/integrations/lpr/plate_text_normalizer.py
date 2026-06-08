"""Normalización y filtrado de candidatos de placa.

El OCR suele devolver espacios, guiones, puntos o caracteres confundidos. Este
módulo concentra esas reglas para mantener el cliente OCR simple y testeable.
"""

from __future__ import annotations

import re

_ALLOWED_CHARS_PATTERN = re.compile(r"[^A-Z0-9]")


class PlateTextNormalizer:
    def __init__(self, min_length: int = 5, max_length: int = 8) -> None:
        self._min_length = min_length
        self._max_length = max_length

    def normalize(self, raw_text: str) -> str:
        """Convierte texto OCR crudo a un candidato alfanumérico limpio."""
        text = raw_text.upper().strip()
        text = _ALLOWED_CHARS_PATTERN.sub("", text)
        return text

    def is_candidate(self, text: str) -> bool:
        """Valida si el texto tiene forma mínima plausible de placa."""
        if not text:
            return False
        if len(text) < self._min_length or len(text) > self._max_length:
            return False
        return any(char.isalpha() for char in text) and any(char.isdigit() for char in text)