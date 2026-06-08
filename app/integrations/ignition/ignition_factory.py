"""Construcción del `IgnitionJsonWriter`."""

from app.core.config import Settings, get_settings
from app.integrations.ignition.ignition_json_writer import IgnitionJsonWriter


def build_ignition_writer(settings: Settings | None = None) -> IgnitionJsonWriter:
    settings = settings or get_settings()
    return IgnitionJsonWriter(output_dir=settings.ignition_json_output_dir)
