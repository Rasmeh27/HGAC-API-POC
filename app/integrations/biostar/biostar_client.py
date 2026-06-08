"""Cliente HTTP para BioStar 2.

Refactor del script `test_biostar.py` original (procedural) a una clase
con responsabilidades claras:

* gestiona sesión persistente (`bs-session-id`),
* expone operaciones tipadas,
* no decide nada de negocio (eso vive en `BioStarService`),
* no conoce nada sobre cómo se loguea el resultado ni cómo se cachea.

SSL: BioStar 2 suele usar certificado autofirmado en LAN portuaria. La
desactivación de verificación SSL viene solo por configuración explícita.
"""

from __future__ import annotations

from typing import Any, Optional

import requests
import urllib3
from loguru import logger

from app.core.errors import (
    BioStarAuthenticationError,
    BioStarError,
    BioStarUserNotFoundError,
)


class BioStarClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
        timeout_seconds: int = 10,
    ) -> None:
        if not base_url or not username or not password:
            raise BioStarError("BioStar host/username/password no configurados")

        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._timeout = timeout_seconds

        self._session: Optional[requests.Session] = None
        self._session_id: Optional[str] = None

        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # ---- ciclo de vida de la sesión ----

    def login(self) -> None:
        session = requests.Session()
        session.verify = self._verify_ssl

        url = f"{self._base_url}/api/login"
        payload = {"User": {"login_id": self._username, "password": self._password}}
        logger.debug("BioStar login -> {}", url)
        response = session.post(url, json=payload, timeout=self._timeout)
        if response.status_code != 200:
            raise BioStarAuthenticationError(
                f"Login fallido ({response.status_code}): {response.text}"
            )

        session_id = response.headers.get("bs-session-id")
        if not session_id:
            raise BioStarAuthenticationError("BioStar no devolvió bs-session-id")

        session.headers.update({"bs-session-id": session_id})
        self._session = session
        self._session_id = session_id
        logger.info("BioStar: sesión iniciada")

    def logout(self) -> None:
        if not self._session:
            return
        try:
            self._session.post(f"{self._base_url}/api/logout", timeout=self._timeout)
        except requests.RequestException as exc:
            logger.warning("Error en logout BioStar (ignorado): {}", exc)
        finally:
            self._session.close()
            self._session = None
            self._session_id = None

    def __enter__(self) -> "BioStarClient":
        self.login()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.logout()

    # ---- operaciones ----

    def get_users(self, limit: int = 100) -> list[dict[str, Any]]:
        data = self._get("/api/users", params={"limit": limit})
        return data.get("UserCollection", {}).get("rows", [])

    def get_user_detail(self, user_id: str) -> dict[str, Any]:
        data = self._get(f"/api/users/{user_id}")
        user = data.get("User")
        if not user:
            raise BioStarUserNotFoundError(f"Usuario {user_id} no existe")
        return user

    def get_devices(self) -> list[dict[str, Any]]:
        data = self._get("/api/devices")
        return data.get("DeviceCollection", {}).get("rows", [])

    # ---- helpers ----

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if not self._session:
            raise BioStarError("BioStarClient no autenticado; llama a login() primero")

        url = f"{self._base_url}{path}"
        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
        except requests.RequestException as exc:
            raise BioStarError(f"Error de red en {path}: {exc}") from exc

        if response.status_code == 401:
            raise BioStarAuthenticationError("Sesión BioStar expirada")
        if response.status_code >= 400:
            raise BioStarError(
                f"BioStar GET {path} -> {response.status_code}: {response.text}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise BioStarError(f"Respuesta no-JSON en {path}") from exc
