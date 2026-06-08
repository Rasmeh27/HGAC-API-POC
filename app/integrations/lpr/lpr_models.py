"""Modelos de dominio para LPR.

Se exponen al resto del backend en vez de pasar el JSON crudo de
Plate Recognizer. Esto evita acoplarnos a su esquema.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LprResult(BaseModel):
    plate: str = Field(..., description="Texto de la placa detectada")
    confidence: float = Field(..., ge=0, le=1)
    vehicle_type: Optional[str] = Field(default=None, description="Ej: Car, Truck, Bus")
    region: Optional[str] = Field(default=None, description="Código ISO de región/país")
    timestamp: datetime
    status: str = Field(default="OK", description="OK | NO_PLATE | API_ERROR")
