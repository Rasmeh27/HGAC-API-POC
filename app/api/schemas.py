"""Modelos request/response de la capa HTTP.

Se separan deliberadamente de los modelos de dominio para no acoplar el
contrato API a representaciones internas. Si el dominio cambia un
campo interno, los clientes HTTP no se rompen mientras esta capa
mantenga el shape esperado.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---- LPR ----

class LprReadRequest(BaseModel):
    """No requiere cuerpo en la PoC: captura del provider configurado."""


class LprReadResponse(BaseModel):
    plate: str
    confidence: float
    vehicle_type: Optional[str] = None
    region: Optional[str] = None
    status: str
    timestamp: datetime


class LprSnapshotResponse(BaseModel):
    filename: str
    path: str
    size_bytes: int
    captured_at: datetime


# ---- BioStar ----

class BioStarVerifyRequest(BaseModel):
    nombre_o_id: str = Field(..., min_length=1)


class BioStarVerifyResponse(BaseModel):
    found: bool
    is_active: bool
    user_id: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    reason: Optional[str] = None
    checked_at: datetime


# ---- RNTT ----

class RnttLookupRequest(BaseModel):
    placa: str = Field(..., min_length=1)


class RnttPolicyDto(BaseModel):
    name: str
    expires_at: Optional[str] = None
    is_valid: bool


class RnttVehicleDto(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    year: Optional[int] = None


class RnttLookupResponse(BaseModel):
    plate: str
    status: str
    vehicle: Optional[RnttVehicleDto] = None
    policies: List[RnttPolicyDto] = []
    queried_at: datetime


# ---- Crossing ----

class CrossingEvaluateRequest(BaseModel):
    gate_id: str = Field(..., min_length=1)
    lane_id: str = Field(..., min_length=1)
    driver_identifier: Optional[str] = None


class CrossingEvaluateResponse(BaseModel):
    decision: str
    reason: str
    plate: Optional[str] = None
    rntt_status: Optional[str] = None
    biostar_found: Optional[bool] = None
    biostar_active: Optional[bool] = None
    evaluated_at: datetime