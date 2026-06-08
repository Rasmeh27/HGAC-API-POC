"""Selección del cliente RNTT según configuración."""

from app.core.config import Settings, get_settings
from app.integrations.rntt.rntt_client import RnttClient, SeleniumRnttClient, StubRnttClient
from app.integrations.rntt.rntt_service import RnttService


def build_rntt_client(settings: Settings | None = None) -> RnttClient:
    settings = settings or get_settings()
    if settings.rntt_use_stub:
        return StubRnttClient()
    return SeleniumRnttClient(
        portal_url=settings.rntt_portal_url,
        timeout_seconds=settings.rntt_timeout_seconds,
        headless=settings.rntt_headless,
    )


def build_rntt_service(settings: Settings | None = None) -> RnttService:
    return RnttService(client=build_rntt_client(settings))
