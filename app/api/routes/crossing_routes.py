"""Endpoint de evaluación de cruce vehicular."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.dependencies import crossing_service_provider
from app.api.schemas import CrossingEvaluateRequest, CrossingEvaluateResponse
from app.modules.crossing.crossing_models import CrossingEvent
from app.modules.crossing.crossing_service import CrossingService

router = APIRouter(prefix="/crossing", tags=["Crossing"])


@router.post("/evaluate", response_model=CrossingEvaluateResponse)
def evaluate_crossing(
    payload: CrossingEvaluateRequest,
    crossing_service: CrossingService = Depends(crossing_service_provider),
) -> CrossingEvaluateResponse:
    event = CrossingEvent(
        gate_id=payload.gate_id,
        lane_id=payload.lane_id,
        driver_identifier=payload.driver_identifier,
        requested_at=datetime.now(timezone.utc),
    )
    evaluation = crossing_service.evaluate(event)

    return CrossingEvaluateResponse(
        decision=evaluation.decision.value,
        reason=evaluation.reason,
        plate=evaluation.lpr.plate if evaluation.lpr else None,
        rntt_status=evaluation.rntt.status if evaluation.rntt else None,
        biostar_found=evaluation.biostar.found if evaluation.biostar else None,
        biostar_active=evaluation.biostar.is_active if evaluation.biostar else None,
        evaluated_at=evaluation.evaluated_at,
    )
