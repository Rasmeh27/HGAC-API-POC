"""Endpoint de salud."""

from fastapi import APIRouter, Depends

from app.api.dependencies import settings_provider
from app.core.config import Settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check(settings: Settings = Depends(settings_provider)) -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
