from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VehicleObservationRequest(BaseModel):
    camera_id: str
    gate_id: str
    lane_id: str
    vehicle_type: str = "truck"
    plate: Optional[str] = None
    plate_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    snapshot_path: Optional[str] = None
    timestamp: datetime


class RFIDReadRequest(BaseModel):
    reader_id: str
    gate_id: str
    lane_id: str
    rfid_tag: str
    timestamp: datetime


class AccessDecisionResponse(BaseModel):
    event_id: str
    decision_status: str
    decision_reason: str
    identity_score: float
