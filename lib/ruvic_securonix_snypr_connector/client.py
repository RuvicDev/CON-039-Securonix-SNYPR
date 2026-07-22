"""Cliente para consultar y actualizar incidentes en Securonix SNYPR.

Capacidades:
- list_incidents():          listar incidentes, con filtros opcionales.
- get_incident_detail():     consultar el detalle completo de un incidente.
- update_incident_status():  actualizar el estado de un incidente.

Autenticación: Securonix usa un token generado a partir de usuario y
contraseña (no OAuth ni Basic Auth tradicional) — se solicita una vez
mediante el endpoint de generación de token, y ese token se reutiliza en
las peticiones siguientes hasta que expira. Las credenciales SIEMPRE
provienen de variables de entorno RUVIC_SECURONIX_SNYPR_* (ver
config.SecuronixConfig.from_env). Prohibido hardcodearlas.

Nota sobre las rutas de API: los nombres exactos de los endpoints de
incidentes han variado entre versiones de Securonix (6.3, 6.4, cloud vs
on-prem) y no están completamente documentados en fuentes públicas. Este
cliente usa las rutas más comúnmente documentadas como valores por
defecto, pero son configurables (ver config.py) — verifica contra el
Postman collection o el equipo de Securonix del cliente si tu tenant usa
nombres distintos.
"""

from __future__ import annotations

import time
from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from .config import SecuronixConfig
from .exceptions import (
    SecuronixAuthError,
    SecuronixDataError,
    SecuronixNetworkError,
)
from .logging_utils import get_logger


class SecuronixClient:
    """Cliente de Securonix SNYPR autenticado por token.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_SECURONIX_SNYPR_* (comportamiento
            estándar en el runtime de la plataforma).

    Ejemplo:
        >>> client = SecuronixClient()  # lee RUVIC_SECURONIX_SNYPR_* del entorno
        >>> client.list_incidents(status="Open")
        [{'incident_id': '12345', 'status': 'Open', ...}, ...]
    """

    def __init__(self, config: SecuronixConfig | None = None) -> None:
        self.config = config or SecuronixConfig.from_env()
        self._logger = get_logger()
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------ #
    # Autenticación: generación y caché del token
    # ------------------------------------------------------------------ #

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token

        url = f"{self.config.base_url}{self.config.token_path}"
        try:
            resp = requests.get(
                url,
                headers={
                    "username": self.config.username,
                    "password": self.config.password,
                    "validity": str(self.config.token_validity_days),
                },
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        except Timeout as exc:
            raise SecuronixNetworkError(
                f"Tiempo de espera agotado ({self.config.timeout}s) generando el token en {url}."
            ) from exc
        except RequestsConnectionError as exc:
            raise SecuronixNetworkError(f"No se pudo conectar a {url}: {exc}") from exc
        except RequestException as exc:
            raise SecuronixNetworkError(f"Error de red generando el token: {exc}") from exc

        if resp.status_code != 200:
            raise SecuronixAuthError(
                f"No se pudo generar el token (HTTP {resp.status_code}): {resp.text[:300]}. "
                "Revisa el usuario y la contraseña."
            )

        token = self._extract_token(resp)
        if not token:
            raise SecuronixAuthError(
                f"El servidor respondió sin un token utilizable: {resp.text[:300]}"
            )

        self._token = token
        self._token_expires_at = time.time() + (self.config.token_validity_days * 86400)
        self._logger.info("Token de Securonix generado (validez: %d días)", self.config.token_validity_days)
        return self._token

    @staticmethod
    def _extract_token(resp: requests.Response) -> str:
        """El endpoint de token puede responder como texto plano o como
        JSON con la clave 'token'/'Token', según la versión de Securonix."""
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                for key in ("token", "Token", "result"):
                    if key in payload and payload[key]:
                        return str(payload[key])
            elif isinstance(payload, str):
                return payload.strip()
        except ValueError:
            pass
        return resp.text.strip().strip('"')

    # ------------------------------------------------------------------ #
    # Peticiones autenticadas
    # ------------------------------------------------------------------ #

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None,
                 json_body: dict[str, Any] | None = None) -> requests.Response:
        token = self._get_token()
        url = f"{self.config.base_url}{path}"
        query = dict(params or {})
        query["token"] = token
        if self.config.tenant_name:
            query["tenantname"] = self.config.tenant_name

        try:
            resp = requests.request(
                method, url, params=query, json=json_body,
                timeout=self.config.timeout, verify=self.config.verify_ssl,
            )
        except Timeout as exc:
            raise SecuronixNetworkError(
                f"Tiempo de espera agotado ({self.config.timeout}s) llamando a {path}."
            ) from exc
        except RequestsConnectionError as exc:
            raise SecuronixNetworkError(f"No se pudo conectar a {url}: {exc}") from exc
        except RequestException as exc:
            raise SecuronixNetworkError(f"Error de red: {exc}") from exc

        if resp.status_code == 401:
            # El token pudo expirar o ser revocado del lado del servidor:
            # se renueva una vez y se reintenta.
            self._token = None
            token = self._get_token()
            query["token"] = token
            try:
                resp = requests.request(
                    method, url, params=query, json=json_body,
                    timeout=self.config.timeout, verify=self.config.verify_ssl,
                )
            except RequestException as exc:
                raise SecuronixNetworkError(f"Error de red: {exc}") from exc
            if resp.status_code == 401:
                raise SecuronixAuthError(
                    "El token fue rechazado incluso tras renovarlo. Revisa el usuario y la contraseña."
                )

        return resp

    def _raise_for_error(self, resp: requests.Response, context: str) -> None:
        message = resp.text[:300] or "Error desconocido"
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                message = payload.get("message") or payload.get("errorMessage") or message
        except ValueError:
            pass

        if resp.status_code == 403:
            raise SecuronixAuthError(
                f"Permisos insuficientes en {context}: {message}. El usuario configurado "
                "necesita acceso al módulo de gestión de incidentes."
            )
        if resp.status_code == 404:
            raise SecuronixDataError(f"No encontrado en {context}: {message}")
        if resp.status_code in (400, 422):
            raise SecuronixDataError(f"Solicitud inválida en {context}: {message}")
        raise SecuronixDataError(
            f"Error de Securonix en {context} (HTTP {resp.status_code}): {message}"
        )

    # ------------------------------------------------------------------ #
    # Ping / prueba de conexión
    # ------------------------------------------------------------------ #

    def ping(self) -> bool:
        """Verifica las credenciales generando un token."""
        self._get_token()
        self._logger.info("Ping exitoso a Securonix SNYPR (%s)", self.config.base_url)
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: listar incidentes
    # ------------------------------------------------------------------ #

    def list_incidents(
        self,
        status: str | None = None,
        priority: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Lista incidentes, con filtros opcionales.

        Args:
            status: filtra por estado (ej. "Open", "Closed"; los valores
                exacatos dependen de la configuración del tenant).
            priority: filtra por prioridad (ej. "Critical", "High").
            from_date / to_date: rango de fechas (formato "MM/dd/yyyy",
                según convención de Securonix).
            max_results: máximo de resultados (default 50).

        Returns:
            Lista de dicts con los incidentes encontrados (la forma exacta
            de cada registro depende de la respuesta del tenant).

        Ejemplo:
            >>> client.list_incidents(status="Open", priority="Critical")
            [{'incidentId': '12345', 'status': 'Open', ...}, ...]
        """
        params: dict[str, Any] = {"max": max_results}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        resp = self._request("GET", self.config.list_incidents_path, params=params)
        if resp.status_code != 200:
            self._raise_for_error(resp, "list_incidents")

        payload = resp.json()
        incidents = self._extract_list(payload)
        self._logger.info("list_incidents: %d resultado(s)", len(incidents))
        return incidents

    @staticmethod
    def _extract_list(payload: Any) -> list[dict[str, Any]]:
        """Securonix envuelve las listas de forma distinta según el
        endpoint/versión — se maneja la variante más común (lista directa,
        o un dict con 'result'/'data'/'incidentItems')."""
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("result", "data", "incidentItems", "incidents"):
                val = payload.get(key)
                if isinstance(val, list):
                    return val
                if isinstance(val, dict):
                    for inner_key in ("incidentItems", "data"):
                        if isinstance(val.get(inner_key), list):
                            return val[inner_key]
        return []

    # ------------------------------------------------------------------ #
    # Capacidad 2: consultar el detalle de un incidente
    # ------------------------------------------------------------------ #

    def get_incident_detail(self, incident_id: str) -> dict[str, Any]:
        """Consulta el detalle completo de un incidente.

        Args:
            incident_id: identificador del incidente.

        Returns:
            Dict con los datos completos del incidente.

        Ejemplo:
            >>> client.get_incident_detail("12345")
            {'incidentId': '12345', 'status': 'Open', 'priority': 'Critical', ...}
        """
        if not incident_id or not str(incident_id).strip():
            raise SecuronixDataError("incident_id no puede estar vacío.")

        resp = self._request(
            "GET", self.config.get_incident_path, params={"incidentId": incident_id}
        )
        if resp.status_code != 200:
            self._raise_for_error(resp, f"get_incident_detail {incident_id}")

        payload = resp.json()
        if isinstance(payload, dict) and "result" in payload and isinstance(payload["result"], dict):
            return payload["result"]
        return payload if isinstance(payload, dict) else {"raw": payload}

    # ------------------------------------------------------------------ #
    # Capacidad 3: actualizar el estado de un incidente
    # ------------------------------------------------------------------ #

    def update_incident_status(
        self, incident_id: str, new_status: str, comment: str | None = None
    ) -> dict[str, Any]:
        """Actualiza el estado de un incidente.

        Args:
            incident_id: identificador del incidente.
            new_status: nuevo estado (los valores válidos dependen de la
                configuración del workflow del tenant, ej. "Closed",
                "In Progress" — confírmalos con `get_incident_detail` o
                con el administrador de Securonix si no los conoces).
            comment: comentario opcional que acompañe el cambio de estado.

        Returns:
            Dict con "incident_id", "status" y "success": True.

        Ejemplo:
            >>> client.update_incident_status("12345", "Closed", comment="Falso positivo confirmado")
            {'incident_id': '12345', 'status': 'Closed', 'success': True}
        """
        if not incident_id or not str(incident_id).strip():
            raise SecuronixDataError("incident_id no puede estar vacío.")
        if not new_status or not new_status.strip():
            raise SecuronixDataError("new_status no puede estar vacío.")

        body = {"incidentId": incident_id, "status": new_status}
        if comment:
            body["comment"] = comment

        resp = self._request("POST", self.config.update_status_path, json_body=body)
        if resp.status_code not in (200, 201, 204):
            self._raise_for_error(resp, f"update_incident_status {incident_id}")

        self._logger.info("Incidente %s actualizado a estado %r", incident_id, new_status)
        return {"incident_id": incident_id, "status": new_status, "success": True}
