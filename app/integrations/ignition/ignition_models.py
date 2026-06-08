"""Esquemas de los archivos JSON que se entregan a Ignition.

El backend ya expone API REST, pero mientras la integración nativa de
Ignition (vía endpoint) no esté lista, podemos depositar archivos JSON
en una carpeta compartida. Estos modelos definen ese contrato.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IgnitionLprPayload(BaseModel):
    event_id: str
    plate: str
    confidence: float
    vehicle_type: Optional[str] = None
    region: Optional[str] = None
    timestamp: datetime


class IgnitionBioStarPayload(BaseModel):
    event_id: str
    user_identifier: str
    found: bool
    is_active: bool
    timestamp: datetime


class IgnitionRnttPayload(BaseModel):
    event_id: str
    plate: str
    status: str
    timestamp: datetime


class IgnitionCrossingDecisionPayload(BaseModel):
    event_id: str
    decision: str
    reason: str
    plate: Optional[str] = None
    user_identifier: Optional[str] = None
    timestamp: datetime
