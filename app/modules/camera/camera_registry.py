"""Registro de cámaras conocidas por el backend.

En esta fase de PoC solo existe una cámara (CAM-P-01, webcam USB). El registro
desacopla el `camera_id` lógico que usa Ignition de la fuente física concreta,
de modo que más adelante se pueda añadir o reapuntar cámaras (p.ej. a RTSP) sin
tocar las rutas ni el servicio.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from app.core.errors import CameraNotFoundError


@dataclass(frozen=True)
class CameraConfig:
    """Definición estática de una cámara.

    `source` es la representación legible/estable que se devuelve a Ignition
    (p.ej. ``USB:0`` o una URL RTSP saneada). `device_index` es el índice real
    de OpenCV para fuentes USB.
    """

    camera_id: str
    camera_name: str
    source_type: str
    source: str
    device_index: int = 0
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int = 0
    roi_height: int = 0

    @property
    def has_lpr_roi(self) -> bool:
        return self.roi_width > 0 and self.roi_height > 0

    @property
    def safe_source(self) -> str:
        if self.source_type != "rtsp":
            return self.source
        parsed = urlsplit(self.source)
        if not parsed.hostname:
            return "rtsp:no-configurado"
        port = f":{parsed.port}" if parsed.port else ""
        return urlunsplit((parsed.scheme, f"{parsed.hostname}{port}", parsed.path, "", ""))


class CameraRegistry:
    """Catálogo en memoria de cámaras disponibles."""

    def __init__(self, cameras: list[CameraConfig] | None = None) -> None:
        self._cameras: dict[str, CameraConfig] = {}
        for camera in cameras if cameras is not None else _default_cameras():
            self.register(camera)

    def register(self, camera: CameraConfig) -> None:
        self._cameras[camera.camera_id] = camera

    def get(self, camera_id: str) -> CameraConfig:
        """Devuelve la cámara o lanza `CameraNotFoundError` si no existe."""
        try:
            return self._cameras[camera_id]
        except KeyError as exc:
            raise CameraNotFoundError(
                f"Cámara '{camera_id}' no registrada"
            ) from exc

    def all(self) -> list[CameraConfig]:
        return list(self._cameras.values())

    @classmethod
    def from_json(cls, path: str | Path) -> "CameraRegistry":
        registry_path = Path(path)
        if not registry_path.exists():
            return cls()

        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        rows = payload.get("cameras", []) if isinstance(payload, dict) else payload
        cameras: list[CameraConfig] = []
        for row in rows:
            source = str(row.get("source", ""))
            source_env = str(row.get("source_env", "")).strip()
            if source_env:
                source = os.environ.get(source_env, "")
            roi = row.get("lpr_roi") or {}
            cameras.append(
                CameraConfig(
                    camera_id=str(row["camera_id"]),
                    camera_name=str(row.get("camera_name", row["camera_id"])),
                    source_type=str(row.get("source_type", "rtsp")),
                    source=source,
                    device_index=int(row.get("device_index", 0)),
                    roi_x=int(roi.get("x", 0)),
                    roi_y=int(roi.get("y", 0)),
                    roi_width=int(roi.get("width", 0)),
                    roi_height=int(roi.get("height", 0)),
                )
            )
        return cls(cameras=cameras)


def _default_cameras() -> list[CameraConfig]:
    """Cámaras de la PoC. Hoy solo la webcam USB local."""
    return [
        CameraConfig(
            camera_id="CAM-P-01",
            camera_name="Cámara USB PoC",
            source_type="usb",
            source="USB:0",
            device_index=0,
        ),
    ]
