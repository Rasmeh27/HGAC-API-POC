"""Orquestación de captura + reconocimiento de placa."""

from __future__ import annotations

from loguru import logger

from app.core.errors import LprPlateNotDetectedError
from app.integrations.camera.camera_provider import CameraProvider
from app.integrations.lpr.lpr_client import LprClient
from app.integrations.lpr.lpr_models import LprResult


class LprService:
    def __init__(
        self,
        camera_provider: CameraProvider,
        lpr_client: LprClient,
        min_confidence: float = 0.5,
    ) -> None:
        self._camera = camera_provider
        self._client = lpr_client
        self._min_confidence = min_confidence

    def capture_snapshot(self) -> bytes:
        """Captura un frame JPEG desde la cámara configurada."""
        logger.info("LPR: capturando snapshot de cámara...")
        return self._camera.capture_frame()

    def read_plate(self) -> LprResult:
        """Captura un frame y lo procesa con el proveedor LPR configurado."""
        frame_bytes = self.capture_snapshot()
        logger.info("LPR: procesando frame ({} bytes)", len(frame_bytes))
        result = self._client.recognize(frame_bytes)

        if result.confidence < self._min_confidence:
            raise LprPlateNotDetectedError(
                f"Confianza insuficiente: {result.confidence:.2f} < {self._min_confidence:.2f}"
            )

        return result