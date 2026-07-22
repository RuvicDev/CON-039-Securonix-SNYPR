"""Conector Ruvic para Securonix SNYPR (gestión de incidentes)."""

from .client import SecuronixClient
from .config import ENV_PREFIX, SecuronixConfig
from .exceptions import (
    SecuronixAuthError,
    SecuronixConfigError,
    SecuronixConnectorError,
    SecuronixDataError,
    SecuronixNetworkError,
)
from .logging_utils import setup_logging

__all__ = [
    "ENV_PREFIX",
    "SecuronixAuthError",
    "SecuronixClient",
    "SecuronixConfig",
    "SecuronixConfigError",
    "SecuronixConnectorError",
    "SecuronixDataError",
    "SecuronixNetworkError",
    "setup_logging",
]

__version__ = "1.0.0"
