"""Reglas de decisión de cruce.

Función pura: recibe los resultados ya recolectados de cada integración
y devuelve `(decision, reason)`. No hace IO, no llama a servicios. Esto
la hace trivialmente testeable.

Reglas (en orden de prioridad):
1. Sin placa detectada -> NEEDS_MANUAL_REVIEW.
2. Placa detectada pero RNTT falló -> NEEDS_MANUAL_REVIEW.
3. RNTT indica vehículo inactivo o pólizas vencidas -> REJECTED.
4. BioStar consultado y usuario inactivo o no encontrado -> REJECTED.
5. Todo válido -> AUTHORIZED.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

from app.integrations.biostar.biostar_models import BioStarVerificationResult
from app.integrations.lpr.lpr_models import LprResult
from app.integrations.rntt.rntt_models import RnttResult
from app.modules.crossing.crossing_models import CrossingDecision


def evaluate_crossing(
    lpr: Optional[LprResult],
    rntt: Optional[RnttResult],
    biostar: Optional[BioStarVerificationResult],
    today: Optional[date] = None,
) -> Tuple[CrossingDecision, str]:
    if lpr is None or not lpr.plate:
        return CrossingDecision.NEEDS_MANUAL_REVIEW, "Placa no detectada"

    if rntt is None:
        return CrossingDecision.NEEDS_MANUAL_REVIEW, "Consulta RNTT falló"

    if rntt.status.upper() == "NOT_FOUND":
        return CrossingDecision.NEEDS_MANUAL_REVIEW, "Placa no existe en RNTT"

    if rntt.status.upper() != "ACTIVE":
        return CrossingDecision.REJECTED, f"RNTT indica vehículo {rntt.status}"

    reference_day = today or date.today()
    expired = [
        p for p in rntt.policies
        if not p.is_valid or (p.expires_at is not None and p.expires_at < reference_day)
    ]
    if expired:
        nombres = ", ".join(p.name for p in expired)
        return CrossingDecision.REJECTED, f"Pólizas vencidas: {nombres}"

    if biostar is not None:
        if not biostar.found:
            return CrossingDecision.REJECTED, "Chofer no encontrado en BioStar"
        if not biostar.is_active:
            return CrossingDecision.REJECTED, "Chofer inactivo en BioStar"

    return CrossingDecision.AUTHORIZED, "Todos los controles válidos"
