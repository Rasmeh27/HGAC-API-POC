"""Modelos limpios para datos de RNTT (Registro Nacional de Tránsito Terrestre)."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RnttPolicy(BaseModel):
    name: str
    expires_at: Optional[date] = None
    is_valid: bool = True


class RnttVehicle(BaseModel):
    plate: str
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    year: Optional[int] = None


class RnttResult(BaseModel):
    plate: str
    status: str = Field(..., description="ACTIVE | INACTIVE | NOT_FOUND")
    vehicle: Optional[RnttVehicle] = None
    policies: List[RnttPolicy] = []
    queried_at: datetime
