"""Modelos del flujo principal de cruce vehicular."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.integrations.biostar.biostar_models import BioStarVerificationResult
from app.integrations.lpr.lpr_models import LprResult
from app.integrations.rntt.rntt_models import RnttResult


class CrossingDecision(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"


class CrossingEvent(BaseModel):
    """Entrada al servicio de cruce.

    `driver_identifier` es opcional: cuando RFID/lectora identifica al
    chofer (por nombre o user_id) se pasa; si no, BioStar simplemente no
    se consulta y la regla lo trata como información ausente.
    """

    gate_id: str
    lane_id: str
    driver_identifier: Optional[str] = Field(
        default=None,
        description="user_id o nombre del chofer (opcional)",
    )
    requested_at: datetime


class CrossingEvaluation(BaseModel):
    """Resultado de evaluar las reglas sobre los datos recolectados."""

    decision: CrossingDecision
    reason: str
    lpr: Optional[LprResult] = None
    rntt: Optional[RnttResult] = None
    biostar: Optional[BioStarVerificationResult] = None
    evaluated_at: datetime
