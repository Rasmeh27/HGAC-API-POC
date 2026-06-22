"""Resultado de clasificar una placa contra el catálogo dominicano."""

from __future__ import annotations

from dataclasses import dataclass

# Códigos de clasificación (estables; útiles para tags Ignition / decisiones).
CODE_UNKNOWN = "UNKNOWN"

VEHICLE_TYPE_UNKNOWN = "unknown"


@dataclass(frozen=True)
class PlateClassification:
    """Clasificación de una placa normalizada.

    - `code`: código estable del tipo (p.ej. `PRIVATE_AUTO`, `OFICIAL`, `UNKNOWN`).
    - `label`: etiqueta legible en español (p.ej. "Automóvil privado").
    - `vehicle_type`: tipo de vehículo asociado (p.ej. `automovil_privado`).
    - `pattern`: regex del patrón que casó (vacío si no casó ninguno).
    - `prefix`: prefijo alfabético inicial de la placa (p.ej. `A`, `OF`, `PP`).
    - `priority`: prioridad del patrón (mayor = más específico/preferente).
    - `is_valid`: si la placa casó algún patrón del catálogo.
    """

    code: str
    label: str
    vehicle_type: str
    pattern: str
    prefix: str
    priority: int
    is_valid: bool

    @classmethod
    def unknown(cls, prefix: str = "") -> "PlateClassification":
        return cls(
            code=CODE_UNKNOWN,
            label="No catalogada",
            vehicle_type=VEHICLE_TYPE_UNKNOWN,
            pattern="",
            prefix=prefix,
            priority=0,
            is_valid=False,
        )
