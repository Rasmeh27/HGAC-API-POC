"""Modelos limpios para datos de BioStar 2.

Estos modelos son los que se exponen al resto del backend. No exponemos
la respuesta cruda del API porque su esquema cambia entre versiones.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BioStarUser(BaseModel):
    user_id: str
    name: str
    is_active: bool = True
    email: Optional[str] = None
    department: Optional[str] = None


class BioStarDevice(BaseModel):
    device_id: str
    name: str
    status: Optional[str] = None


class BioStarVerificationResult(BaseModel):
    """Resultado de `BioStarService.verificar_usuario`."""

    found: bool
    is_active: bool = False
    user: Optional[BioStarUser] = None
    reason: Optional[str] = Field(
        default=None,
        description="Motivo cuando found=False o is_active=False",
    )
    checked_at: datetime
