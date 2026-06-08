"""Construcción del `CrossingService` con todas sus dependencias."""

from app.core.config import Settings, get_settings
from app.integrations.biostar.biostar_factory import build_biostar_service
from app.integrations.lpr.lpr_factory import build_lpr_service
from app.integrations.rntt.rntt_factory import build_rntt_service
from app.modules.crossing.crossing_service import CrossingService


def build_crossing_service(settings: Settings | None = None) -> CrossingService:
    settings = settings or get_settings()

    biostar_service = None
    if settings.biostar_host and settings.biostar_username and settings.biostar_password:
        biostar_service = build_biostar_service(settings)

    return CrossingService(
        lpr_service=build_lpr_service(settings),
        rntt_service=build_rntt_service(settings),
        biostar_service=biostar_service,
    )
