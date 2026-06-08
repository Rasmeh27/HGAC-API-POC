"""Contrato común para motores LPR.

El resto del backend no debe depender del proveedor concreto de LPR. Para la
PoC podemos usar OCR local gratuito y, si hace falta, cambiar luego a un motor
comercial o entrenado sin tocar `LprService` ni `/crossing/evaluate`.
"""

from abc import ABC, abstractmethod

from app.integrations.lpr.lpr_models import LprResult


class LprClient(ABC):
    """Puerto de integración para reconocimiento de placas."""

    @abstractmethod
    def recognize(self, image_bytes: bytes) -> LprResult:
        """Reconoce una placa desde una imagen JPEG."""