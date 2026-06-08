"""Endpoints para disparar lecturas LPR puntuales y snapshots de diagnóstico."""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import lpr_service_provider, settings_provider
from app.api.schemas import LprReadResponse, LprSnapshotResponse
from app.core.config import Settings
from app.core.errors import (
    CameraError,
    CameraNotAvailableError,
    LprApiError,
    LprPlateNotDetectedError,
)
from app.integrations.lpr.lpr_service import LprService

router = APIRouter(prefix="/lpr", tags=["LPR"])


@router.post("/read", response_model=LprReadResponse)
def read_plate(
    lpr_service: LprService = Depends(lpr_service_provider),
) -> LprReadResponse:
    try:
        result = lpr_service.read_plate()
    except CameraNotAvailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except CameraError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc
    except LprPlateNotDetectedError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except LprApiError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return LprReadResponse(
        plate=result.plate,
        confidence=result.confidence,
        vehicle_type=result.vehicle_type,
        region=result.region,
        status=result.status,
        timestamp=result.timestamp,
    )


@router.post("/debug/snapshot", response_model=LprSnapshotResponse)
def capture_debug_snapshot(
    lpr_service: LprService = Depends(lpr_service_provider),
    settings: Settings = Depends(settings_provider),
) -> LprSnapshotResponse:
    try:
        frame_bytes = lpr_service.capture_snapshot()
    except CameraNotAvailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except CameraError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc

    captured_at = datetime.now(timezone.utc)
    filename = f"snapshot_{captured_at.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    output_dir = Path(settings.evidence_base_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_bytes(frame_bytes)

    return LprSnapshotResponse(
        filename=filename,
        path=str(output_path),
        size_bytes=len(frame_bytes),
        captured_at=captured_at,
    )