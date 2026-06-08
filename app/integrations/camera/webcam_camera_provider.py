"""Captura desde webcam local usando OpenCV."""

from __future__ import annotations

import cv2
from loguru import logger

from app.core.errors import CameraNotAvailableError, CameraTimeoutError
from app.integrations.camera.camera_provider import CameraProvider


class WebcamCameraProvider(CameraProvider):
    def __init__(self, device_index: int = 0, jpeg_quality: int = 90) -> None:
        self._device_index = device_index
        self._jpeg_quality = jpeg_quality

    def capture_frame(self) -> bytes:
        logger.debug("Abriendo webcam index={}", self._device_index)
        capture = cv2.VideoCapture(self._device_index)
        if not capture.isOpened():
            raise CameraNotAvailableError(
                f"No se pudo abrir la webcam (index={self._device_index})"
            )

        try:
            success, frame = capture.read()
            if not success or frame is None:
                raise CameraTimeoutError("La webcam no devolvió frame")

            ok, buffer = cv2.imencode(
                ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self._jpeg_quality]
            )
            if not ok:
                raise CameraTimeoutError("No se pudo codificar el frame a JPEG")
            return buffer.tobytes()
        finally:
            capture.release()
