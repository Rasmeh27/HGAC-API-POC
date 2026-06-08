"""Dependencias FastAPI para inyectar servicios en las rutas.

Centralizar las dependencias evita instanciar servicios pesados (cámara,
sesión BioStar) en cada request y permite sustituirlos fácilmente en
tests con `app.dependency_overrides`.
"""

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.integrations.biostar.biostar_factory import build_biostar_service
from app.integrations.biostar.biostar_service import BioStarService
from app.integrations.ignition.ignition_factory import build_ignition_writer
from app.integrations.ignition.ignition_json_writer import IgnitionJsonWriter
from app.integrations.lpr.lpr_factory import build_lpr_service
from app.integrations.lpr.lpr_service import LprService
from app.integrations.rntt.rntt_factory import build_rntt_service
from app.integrations.rntt.rntt_service import RnttService
from app.modules.crossing.crossing_factory import build_crossing_service
from app.modules.crossing.crossing_service import CrossingService


def settings_provider() -> Settings:
    return get_settings()


@lru_cache
def _cached_lpr_service() -> LprService:
    return build_lpr_service()


@lru_cache
def _cached_rntt_service() -> RnttService:
    return build_rntt_service()


@lru_cache
def _cached_biostar_service() -> BioStarService:
    return build_biostar_service()


@lru_cache
def _cached_crossing_service() -> CrossingService:
    return build_crossing_service()


@lru_cache
def _cached_ignition_writer() -> IgnitionJsonWriter:
    return build_ignition_writer()


def lpr_service_provider() -> LprService:
    return _cached_lpr_service()


def rntt_service_provider() -> RnttService:
    return _cached_rntt_service()


def biostar_service_provider() -> BioStarService:
    return _cached_biostar_service()


def crossing_service_provider() -> CrossingService:
    return _cached_crossing_service()


def ignition_writer_provider() -> IgnitionJsonWriter:
    return _cached_ignition_writer()
