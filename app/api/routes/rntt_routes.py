"""Endpoint de consulta RNTT."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import rntt_service_provider
from app.api.schemas import (
    RnttLookupRequest,
    RnttLookupResponse,
    RnttPolicyDto,
    RnttVehicleDto,
)
from app.core.errors import RnttError, RnttTimeoutError
from app.integrations.rntt.rntt_service import RnttService

router = APIRouter(prefix="/rntt", tags=["RNTT"])


@router.post("/lookup", response_model=RnttLookupResponse)
def lookup_plate(
    payload: RnttLookupRequest,
    rntt_service: RnttService = Depends(rntt_service_provider),
) -> RnttLookupResponse:
    try:
        result = rntt_service.consultar_placa(payload.placa)
    except RnttTimeoutError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc
    except RnttError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return RnttLookupResponse(
        plate=result.plate,
        status=result.status,
        vehicle=(
            RnttVehicleDto(
                brand=result.vehicle.brand,
                model=result.vehicle.model,
                color=result.vehicle.color,
                year=result.vehicle.year,
            )
            if result.vehicle else None
        ),
        policies=[
            RnttPolicyDto(
                name=p.name,
                expires_at=p.expires_at.isoformat() if p.expires_at else None,
                is_valid=p.is_valid,
            )
            for p in result.policies
        ],
        queried_at=result.queried_at,
    )
