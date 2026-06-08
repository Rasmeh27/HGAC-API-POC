"""Selecciona la implementación de `CameraProvider` según configuración."""

from app.core.config import Settings, get_settings
from app.integrations.camera.camera_provider import CameraProvider
from app.integrations.camera.rtsp_camera_provider import RtspCameraProvider
from app.integrations.camera.webcam_camera_provider import WebcamCameraProvider


def build_camera_provider(settings: Settings | None = None) -> CameraProvider:
    settings = settings or get_settings()
    if settings.camera_provider == "rtsp":
        return RtspCameraProvider(rtsp_url=settings.rtsp_url)
    return WebcamCameraProvider(device_index=settings.webcam_index)
