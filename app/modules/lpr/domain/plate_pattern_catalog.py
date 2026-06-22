"""Catálogo de patrones de placa dominicana (referencia operativa DGII).

Convierte una placa normalizada (A-Z0-9, sin separadores) en una
`PlateClassification`. El catálogo es testeable e independiente del motor OCR.

Prioridades (mayor = más específico): oficiales > provisional > exonerada/dealer
> clases de un prefijo + 6 dígitos > motocicleta. La prioridad alimenta el
scoring/decisión del servicio; no implica jerarquía legal.
"""

from __future__ import annotations

import re

from app.modules.lpr.domain.plate_classification import PlateClassification
from app.modules.lpr.domain.plate_pattern import PlatePattern

_PREFIX_RE = re.compile(r"^[A-Z]+")

# tipos de vehículo (strings estables)
_AUTO = "automovil_privado"
_JEEPETA = "jeepeta"
_CARGA = "carga"
_REMOLQUE = "remolque"
_MAQUINA = "maquina_pesada"
_MONTACARGAS = "montacargas"
_PROVISIONAL = "provisional_electronica"
_EXONERADA = "exonerada"
_DEALER = "dealer"
_OFICIAL = "oficial"
_MOTO = "motocicleta"

# Orden de evaluación: los patrones más específicos (2 letras, longitudes fijas)
# primero; la motocicleta (letra variable + 7 dígitos) al final.
DEFAULT_DOMINICAN_PLATE_PATTERNS: tuple[PlatePattern, ...] = (
    PlatePattern("OFICIAL", "Oficial", _OFICIAL, "OF/OP/OE/OM", r"(?:OF|OP|OE|OM)[0-9]{5}", 90),
    PlatePattern("PROVISIONAL_ELECTRONICA", "Placa provisional electrónica", _PROVISIONAL, "PP", r"PP[0-9]{6}", 85),
    PlatePattern("EXONERADA", "Exonerada", _EXONERADA, "EX", r"EX[0-9]{5}", 80),
    PlatePattern("DEALER", "Dealer", _DEALER, "DD", r"DD[0-9]{5}", 80),
    PlatePattern("PRIVATE_AUTO", "Automóvil privado", _AUTO, "A", r"A[0-9]{6}", 70),
    PlatePattern("JEEPETA", "Jeepeta", _JEEPETA, "G", r"G[0-9]{6}", 70),
    PlatePattern("CARGA", "Carga", _CARGA, "L", r"L[0-9]{6}", 70),
    PlatePattern("REMOLQUE", "Remolque", _REMOLQUE, "F", r"F[0-9]{6}", 70),
    PlatePattern("MAQUINA_PESADA", "Máquina pesada", _MAQUINA, "U", r"U[0-9]{6}", 70),
    PlatePattern("MONTACARGAS", "Montacargas", _MONTACARGAS, "J", r"J[0-9]{6}", 70),
    PlatePattern("MOTOCICLETA", "Motocicleta", _MOTO, "", r"[A-Z][0-9]{7}", 60),
)


def plate_prefix(normalized_plate: str) -> str:
    """Prefijo alfabético inicial de la placa (p.ej. `A`, `OF`, `PP`). Vacío si no hay."""
    match = _PREFIX_RE.match(normalized_plate or "")
    return match.group(0) if match else ""


class DominicanPlatePatternCatalog:
    """Catálogo operativo de patrones de placa dominicana."""

    def __init__(self, patterns: tuple[PlatePattern, ...] = DEFAULT_DOMINICAN_PLATE_PATTERNS) -> None:
        self._patterns = patterns
        self._compiled = [(p, re.compile(rf"^{p.regex}$")) for p in patterns]

    def classify(self, normalized_plate: str) -> PlateClassification:
        prefix = plate_prefix(normalized_plate)
        if not normalized_plate:
            return PlateClassification.unknown(prefix)

        # Entre coincidencias, gana la de mayor prioridad (orden estable del catálogo).
        best: PlatePattern | None = None
        for pattern, compiled in self._compiled:
            if compiled.fullmatch(normalized_plate) and (best is None or pattern.priority > best.priority):
                best = pattern

        if best is None:
            return PlateClassification.unknown(prefix)

        return PlateClassification(
            code=best.code,
            label=best.label,
            vehicle_type=best.vehicle_type,
            pattern=best.regex,
            prefix=prefix,
            priority=best.priority,
            is_valid=True,
        )

    def is_valid(self, normalized_plate: str) -> bool:
        return self.classify(normalized_plate).is_valid

    def get_expected_patterns(self) -> list[str]:
        """Lista legible `CODE: regex` de los patrones soportados (para depuración)."""
        return [f"{p.code}: ^{p.regex}$" for p in self._patterns]
