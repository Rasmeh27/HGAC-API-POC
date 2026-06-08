"""Cliente HTTP para Plate Recognizer.

Se conserva como proveedor opcional. La PoC gratuita debe usar
`LPR_PROVIDER=local`, pero mantener este cliente permite comparar resultados o
activar fallback comercial más adelante sin cambiar la capa de aplicación.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests
from loguru import logger

from app.core.errors import LprApiError, LprPlateNotDetectedError
from app.integrations.lpr.lpr_client import LprClient
from app.integrations.lpr.lpr_models import LprResult


class PlateRecognizerClient(LprClient):
    def __init__(
        self,
        api_token: str,
        api_url: str,
        regions: str = "do",
        timeout_seconds: int = 10,
    ) -> None:
        if not api_token:
            logger.warning("PLATE_RECOGNIZER_API_TOKEN está vacío")
        self._api_token = api_token
        self._api_url = api_url
        self._regions = regions
        self._timeout = timeout_seconds

    def recognize(self, image_bytes: bytes) -> LprResult:
        """Envía la imagen y devuelve un resultado LPR normalizado."""
        raw_response = self._request_plate_recognizer(image_bytes)
        return self._parse_response(raw_response)

    def _request_plate_recognizer(self, image_bytes: bytes) -> dict[str, Any]:
        headers = {"Authorization": f"Token {self._api_token}"}
        files = {"upload": ("frame.jpg", image_bytes, "image/jpeg")}
        data = {"regions": self._regions}

        try:
            response = requests.post(
                self._api_url,
                headers=headers,
                files=files,
                data=data,
                timeout=self._timeout,
            )
        except requests.Timeout as exc:
            raise LprApiError("Timeout llamando a Plate Recognizer") from exc
        except requests.RequestException as exc:
            raise LprApiError(f"Error de red con Plate Recognizer: {exc}") from exc

        if response.status_code >= 400:
            raise LprApiError(
                f"Plate Recognizer respondió {response.status_code}: {response.text}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise LprApiError("Respuesta de Plate Recognizer no es JSON") from exc

    def _parse_response(self, raw: dict[str, Any]) -> LprResult:
        results = raw.get("results") or []
        if not results:
            raise LprPlateNotDetectedError("Plate Recognizer no devolvió placas")

        best = results[0]
        vehicle_info = best.get("vehicle") or {}
        return LprResult(
            plate=str(best.get("plate", "")).upper(),
            confidence=float(best.get("score", 0)),
            vehicle_type=vehicle_info.get("type"),
            region=(best.get("region") or {}).get("code"),
            timestamp=datetime.now(timezone.utc),
            status="OK",
        )