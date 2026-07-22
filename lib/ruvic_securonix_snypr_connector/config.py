"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_SECURONIX_SNYPR_.

Nota sobre las rutas de API: Securonix documenta la convención general de
sus endpoints REST (agrupados bajo /ws/...), pero los nombres exactos han
variado entre versiones (6.3, 6.4, cloud vs on-prem). Por eso las 4 rutas
usadas por este conector son CONFIGURABLES, con los valores por defecto
más comunes documentados públicamente — si tu tenant usa nombres
distintos, ajústalos sin necesitar un cambio de código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_SECURONIX_SNYPR_"

_DEFAULT_TOKEN_PATH = "/ws/token/generate"
_DEFAULT_LIST_INCIDENTS_PATH = "/ws/incident/list"
_DEFAULT_GET_INCIDENT_PATH = "/ws/incident/details"
_DEFAULT_UPDATE_STATUS_PATH = "/ws/incident/actions"


@dataclass(frozen=True)
class SecuronixConfig:
    """Parámetros de conexión a un tenant de Securonix SNYPR."""

    base_url: str
    username: str
    password: str
    tenant_name: str = ""
    token_validity_days: int = 365
    verify_ssl: bool = True
    timeout: int = 30
    token_path: str = _DEFAULT_TOKEN_PATH
    list_incidents_path: str = _DEFAULT_LIST_INCIDENTS_PATH
    get_incident_path: str = _DEFAULT_GET_INCIDENT_PATH
    update_status_path: str = _DEFAULT_UPDATE_STATUS_PATH

    @classmethod
    def from_env(cls) -> "SecuronixConfig":
        """Construye la configuración desde las variables RUVIC_SECURONIX_SNYPR_*.

        Raises:
            ValueError: si falta BASE_URL, USERNAME o PASSWORD.
        """
        base_url = os.environ.get(f"{ENV_PREFIX}BASE_URL", "").strip()
        username = os.environ.get(f"{ENV_PREFIX}USERNAME", "").strip()
        password = os.environ.get(f"{ENV_PREFIX}PASSWORD", "")

        missing = [
            name for name, val in (
                (f"{ENV_PREFIX}BASE_URL", base_url),
                (f"{ENV_PREFIX}USERNAME", username),
                (f"{ENV_PREFIX}PASSWORD", password),
            ) if not val
        ]
        if missing:
            raise ValueError(
                "Faltan variables de entorno del conector securonix_snypr: "
                + ", ".join(missing)
                + ". Configura el conector en Settings → Conectores."
            )
        if not (base_url.startswith("https://") or base_url.startswith("http://")):
            raise ValueError(
                f"{ENV_PREFIX}BASE_URL debe incluir el esquema (https:// o http://): {base_url!r}"
            )

        verify_ssl_raw = os.environ.get(f"{ENV_PREFIX}VERIFY_SSL", "true").strip().lower()

        return cls(
            base_url=base_url.rstrip("/"),
            username=username,
            password=password,
            tenant_name=os.environ.get(f"{ENV_PREFIX}TENANT_NAME", "").strip(),
            token_validity_days=int(os.environ.get(f"{ENV_PREFIX}TOKEN_VALIDITY_DAYS", "365")),
            verify_ssl=verify_ssl_raw not in ("false", "0", "no"),
            timeout=int(os.environ.get(f"{ENV_PREFIX}REQUEST_TIMEOUT", "30")),
            token_path=os.environ.get(f"{ENV_PREFIX}TOKEN_PATH", "").strip() or _DEFAULT_TOKEN_PATH,
            list_incidents_path=os.environ.get(f"{ENV_PREFIX}LIST_INCIDENTS_PATH", "").strip()
            or _DEFAULT_LIST_INCIDENTS_PATH,
            get_incident_path=os.environ.get(f"{ENV_PREFIX}GET_INCIDENT_PATH", "").strip()
            or _DEFAULT_GET_INCIDENT_PATH,
            update_status_path=os.environ.get(f"{ENV_PREFIX}UPDATE_STATUS_PATH", "").strip()
            or _DEFAULT_UPDATE_STATUS_PATH,
        )
