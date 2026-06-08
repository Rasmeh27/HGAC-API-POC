"""Abstracción de proveedor de cámara.

Permite intercambiar la fuente de imagen (webcam local, RTSP, futuro Mobotix)
sin que el resto del backend dependa de OpenCV ni de un protocolo concreto.
"""

from abc import ABC, abstractmethod


class CameraProvider(ABC):
    """Contrato mínimo de cualquier fuente de imagen."""

    @abstractmethod
    def capture_frame(self) -> bytes:
        """Captura un frame y lo devuelve codificado como bytes JPEG.

        Debe lanzar `CameraNotAvailableError` si no se puede abrir el dispositivo
        y `CameraTimeoutError` si la captura tarda más del timeout configurado.
        """
