"""Construcción del `LprService` con sus dependencias inyectadas."""

from app.core.config import Settings, get_settings
from app.integrations.camera.camera_factory import build_camera_provider
from app.integrations.lpr.image_preprocessor import RoiConfig
from app.integrations.lpr.local_alpr_client import LocalAlprClient
from app.integrations.lpr.lpr_client import LprClient
from app.integrations.lpr.lpr_service import LprService
from app.integrations.lpr.plate_recognizer_client import PlateRecognizerClient


def build_lpr_service(settings: Settings | None = None) -> LprService:
    settings = settings or get_settings()
    camera = build_camera_provider(settings)
    client = _build_lpr_client(settings)

    return LprService(
        camera_provider=camera,
        lpr_client=client,
        min_confidence=settings.lpr_min_confidence,
    )


def _build_lpr_client(settings: Settings) -> LprClient:
    if settings.lpr_provider == "local":
        roi = None
        if settings.local_lpr_use_fixed_roi:
            roi = RoiConfig(
                x=settings.local_lpr_roi_x,
                y=settings.local_lpr_roi_y,
                width=settings.local_lpr_roi_width,
                height=settings.local_lpr_roi_height,
            )

        return LocalAlprClient(
            roi=roi,
            region=settings.local_lpr_region,
            min_text_length=settings.local_lpr_min_text_length,
            max_text_length=settings.local_lpr_max_text_length,
            gpu=settings.local_lpr_gpu,
        )

    return PlateRecognizerClient(
        api_token=settings.plate_recognizer_api_token,
        api_url=settings.plate_recognizer_api_url,
        regions=settings.plate_recognizer_regions,
        timeout_seconds=settings.plate_recognizer_timeout_seconds,
    )