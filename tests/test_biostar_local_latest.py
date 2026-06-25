import json

import pytest
from fastapi import HTTPException

from app.api.routes.biostar_routes import latest_local_event
from app.core.config import Settings


def test_latest_local_event_returns_monitor_snapshot(tmp_path):
    path = tmp_path / "hgac_biostar_local.json"
    expected = {
        "source": "biostar_local",
        "trigger": True,
        "permitir_paso": True,
        "event_type_code": "4867",
        "nombre": "Byron Russell",
    }
    path.write_text(json.dumps(expected), encoding="utf-8")
    settings = Settings(biostar_local_output_path=str(path))

    assert latest_local_event(settings=settings) == expected


def test_latest_local_event_reports_monitor_not_started(tmp_path):
    settings = Settings(biostar_local_output_path=str(tmp_path / "missing.json"))

    with pytest.raises(HTTPException) as captured:
        latest_local_event(settings=settings)

    assert captured.value.status_code == 503
