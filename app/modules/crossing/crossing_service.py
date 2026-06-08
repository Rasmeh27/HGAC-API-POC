"""Orquesta el flujo de cruce.

1. Recibe un `CrossingEvent`.
2. Pide al `LprService` la placa.
3. Pregunta a RNTT por esa placa.
4. Si el evento trae `driver_identifier`, valida con BioStar.
5. Aplica `evaluate_crossing` y devuelve `CrossingEvaluation`.

Maneja errores de cada integración convirtiéndolos en "dato ausente"
para que las reglas decidan (en general, `NEEDS_MANUAL_REVIEW`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from app.core.errors import (
    BioStarError,
    CameraError,
    IntegrationError,
    LprError,
    RnttError,
)
from app.integrations.biostar.biostar_models import BioStarVerificationResult
from app.integrations.biostar.biostar_service import BioStarService
from app.integrations.lpr.lpr_models import LprResult
from app.integrations.lpr.lpr_service import LprService
from app.integrations.rntt.rntt_models import RnttResult
from app.integrations.rntt.rntt_service import RnttService
from app.modules.crossing.crossing_models import (
    CrossingEvaluation,
    CrossingEvent,
)
from app.modules.crossing.crossing_rules import evaluate_crossing


class CrossingService:
    def __init__(
        self,
        lpr_service: LprService,
        rntt_service: RnttService,
        biostar_service: Optional[BioStarService] = None,
    ) -> None:
        self._lpr = lpr_service
        self._rntt = rntt_service
        self._biostar = biostar_service

    def evaluate(self, event: CrossingEvent) -> CrossingEvaluation:
        lpr_result = self._safe_read_plate()
        rntt_result = self._safe_lookup_plate(lpr_result.plate) if lpr_result else None
        biostar_result = self._safe_verify_driver(event.driver_identifier)

        decision, reason = evaluate_crossing(
            lpr=lpr_result,
            rntt=rntt_result,
            biostar=biostar_result,
        )

        evaluation = CrossingEvaluation(
            decision=decision,
            reason=reason,
            lpr=lpr_result,
            rntt=rntt_result,
            biostar=biostar_result,
            evaluated_at=datetime.now(timezone.utc),
        )
        logger.info(
            "Cruce {}/{} -> {} ({})",
            event.gate_id,
            event.lane_id,
            decision.value,
            reason,
        )
        return evaluation

    # ---- envoltorios seguros ----

    def _safe_read_plate(self) -> Optional[LprResult]:
        try:
            return self._lpr.read_plate()
        except (LprError, CameraError, IntegrationError) as exc:
            logger.warning("LPR no disponible: {}", exc)
            return None

    def _safe_lookup_plate(self, plate: str) -> Optional[RnttResult]:
        try:
            return self._rntt.consultar_placa(plate)
        except RnttError as exc:
            logger.warning("RNTT no disponible para {}: {}", plate, exc)
            return None

    def _safe_verify_driver(self, identifier: Optional[str]) -> Optional[BioStarVerificationResult]:
        if not identifier or self._biostar is None:
            return None
        try:
            return self._biostar.verificar_usuario(identifier)
        except BioStarError as exc:
            logger.warning("BioStar no disponible para '{}': {}", identifier, exc)
            return None
