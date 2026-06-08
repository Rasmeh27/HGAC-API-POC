"""Endpoint de verificación de usuario en BioStar 2."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import biostar_service_provider
from app.api.schemas import BioStarVerifyRequest, BioStarVerifyResponse
from app.core.errors import BioStarAuthenticationError, BioStarError
from app.integrations.biostar.biostar_service import BioStarService

router = APIRouter(prefix="/biostar", tags=["BioStar"])


@router.post("/verify", response_model=BioStarVerifyResponse)
def verify_user(
    payload: BioStarVerifyRequest,
    biostar_service: BioStarService = Depends(biostar_service_provider),
) -> BioStarVerifyResponse:
    try:
        result = biostar_service.verificar_usuario(payload.nombre_o_id)
    except BioStarAuthenticationError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    except BioStarError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return BioStarVerifyResponse(
        found=result.found,
        is_active=result.is_active,
        user_id=result.user.user_id if result.user else None,
        name=result.user.name if result.user else None,
        department=result.user.department if result.user else None,
        reason=result.reason,
        checked_at=result.checked_at,
    )
