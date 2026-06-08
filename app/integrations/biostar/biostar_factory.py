"""Construcción del `BioStarService`."""

from app.core.config import Settings, get_settings
from app.integrations.biostar.biostar_client import BioStarClient
from app.integrations.biostar.biostar_service import BioStarService


def build_biostar_client(settings: Settings | None = None) -> BioStarClient:
    settings = settings or get_settings()
    return BioStarClient(
        base_url=settings.biostar_base_url,
        username=settings.biostar_username,
        password=settings.biostar_password,
        verify_ssl=settings.biostar_verify_ssl,
        timeout_seconds=settings.biostar_timeout_seconds,
    )


def build_biostar_service(settings: Settings | None = None) -> BioStarService:
    return BioStarService(client=build_biostar_client(settings))
