"""Definición de un patrón de placa dominicana.

Referencia operativa: brochure DGII "Tipos de Placas de Vehículos de Motor".
Es un catálogo OPERATIVO para la PoC, NO una fuente legal definitiva: no debe
reemplazar validaciones futuras contra RNTT/Navis/base autorizada.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatePattern:
    """Un patrón de placa: código, etiqueta, tipo de vehículo, regex y prioridad.

    `prefix` es un descriptor legible del prefijo esperado ("A", "OF/OP/OE/OM",
    "" para motocicleta de letra variable); el prefijo real de una placa concreta
    se calcula del texto, no de aquí.
    """

    code: str
    label: str
    vehicle_type: str
    prefix: str
    regex: str
    priority: int

    def matches(self, normalized_plate: str) -> bool:
        return re.fullmatch(self.regex, normalized_plate) is not None
