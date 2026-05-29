from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter

from src.presentation.api.schemas.events import (
    AccessDecisionResponse,
    RFIDReadRequest,
    VehicleObservationRequest,
)

router = APIRouter(prefix="/events", tags=["Events"])

_LAST_RFID_BY_LANE: dict[str, RFIDReadRequest] = {}


@router.post("/rfid-read")
def register_rfid_read(payload: RFIDReadRequest) -> dict:
    lane_key = f"{payload.gate_id}:{payload.lane_id}"
    _LAST_RFID_BY_LANE[lane_key] = payload

    return {
        "success": True,
        "message": "RFID read registered",
        "gate_id": payload.gate_id,
        "lane_id": payload.lane_id,
        "rfid_tag": payload.rfid_tag,
    }


@router.post("/vehicle-observation", response_model=AccessDecisionResponse)
def register_vehicle_observation(payload: VehicleObservationRequest) -> AccessDecisionResponse:
    event_id = f"evt_{uuid4().hex[:12]}"
    lane_key = f"{payload.gate_id}:{payload.lane_id}"
    recent_rfid = _LAST_RFID_BY_LANE.get(lane_key)

    decision_status = "UNKNOWN"
    decision_reason = "NO_RELIABLE_IDENTIFIER"
    identity_score = 0.0

    if payload.plate and recent_rfid:
        decision_status = "AUTHORIZED"
        decision_reason = "PLATE_AND_RFID_PRESENT"
        identity_score = min((payload.plate_confidence or 0.75) + 0.1, 0.95)
    elif payload.plate and not recent_rfid:
        decision_status = "REVIEW_REQUIRED"
        decision_reason = "PLATE_ONLY"
        identity_score = payload.plate_confidence or 0.5
    elif not payload.plate and recent_rfid:
        decision_status = "REVIEW_REQUIRED"
        decision_reason = "RFID_ONLY"
        identity_score = 0.65

    return AccessDecisionResponse(
        event_id=event_id,
        decision_status=decision_status,
        decision_reason=decision_reason,
        identity_score=identity_score,
    )


@router.get("/demo-state")
def get_demo_state() -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "last_rfid_by_lane": {
            lane: rfid.model_dump(mode="json")
            for lane, rfid in _LAST_RFID_BY_LANE.items()
        },
    }
