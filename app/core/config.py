"""Configuración centralizada del backend.

Todas las variables se cargan desde `.env` (o entorno real en producción).
Nunca debe haber credenciales o hosts hardcodeados fuera de este módulo.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "Backend HGAC PoC"
    app_env: str = "development"
    log_level: str = "INFO"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Persistencia / Evidencia (compatibilidad con setup previo) ---
    database_url: str = "sqlite:///./data/hgac_poc.db"
    evidence_base_path: str = "./evidence/snapshots"
    evidence_public_base_url: str = "http://localhost:8000/evidence"

    # --- LPR ---
    # Opciones:
    # - local: OCR gratuito ejecutado dentro del backend.
    # - plate_recognizer: API externa comercial, conservada como fallback.
    lpr_provider: Literal["local", "plate_recognizer"] = "local"
    lpr_min_confidence: float = 0.50

    # --- LPR local gratuito ---
    local_lpr_ocr_engine: Literal["easyocr"] = "easyocr"
    local_lpr_gpu: bool = False
    local_lpr_region: str = "do"
    local_lpr_use_fixed_roi: bool = False
    local_lpr_roi_x: int = 0
    local_lpr_roi_y: int = 0
    local_lpr_roi_width: int = 0
    local_lpr_roi_height: int = 0
    local_lpr_min_text_length: int = 5
    local_lpr_max_text_length: int = 8

    # --- Plate Recognizer (LPR externo opcional) ---
    plate_recognizer_api_token: str = ""
    plate_recognizer_api_url: str = "https://api.platerecognizer.com/v1/plate-reader/"
    plate_recognizer_regions: str = "do"
    plate_recognizer_timeout_seconds: int = 10

    # --- Cámara ---
    camera_provider: Literal["webcam", "rtsp"] = "webcam"
    webcam_index: int = 0
    rtsp_url: str = ""
    camera_capture_timeout_seconds: int = 5

    # --- BioStar 2 ---
    biostar_host: str = ""
    biostar_port: int = 443
    biostar_username: str = ""
    biostar_password: str = ""
    biostar_verify_ssl: bool = False
    biostar_timeout_seconds: int = 10

    # --- RNTT ---
    rntt_portal_url: str = ""
    rntt_timeout_seconds: int = 30
    rntt_headless: bool = True
    rntt_use_stub: bool = True

    # --- Ignition ---
    ignition_json_output_dir: str = "./data/ignition_outbox"
    ignition_base_url: str = "http://localhost:8088"
    ignition_event_endpoint: str = "/system/webdev/hgac/events/vehicle-observation"
    ignition_api_token: str = "change-me"
    ignition_timeout_seconds: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def biostar_base_url(self) -> str:
        scheme = "https" if self.biostar_port == 443 else "http"
        return f"{scheme}://{self.biostar_host}:{self.biostar_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()