"""Excepciones propias del conector Securonix SNYPR.

Separan los tipos de fallo que el usuario debe distinguir: configuración
inválida, autenticación (generación de token), red, y datos (incidente
inexistente, estado inválido, etc.).
"""


class SecuronixConnectorError(Exception):
    """Error base del conector."""


class SecuronixConfigError(SecuronixConnectorError):
    """Configuración inválida: falta un campo requerido."""


class SecuronixAuthError(SecuronixConnectorError):
    """El servidor rechazó la generación del token (usuario/contraseña
    inválidos), o el token generado fue rechazado en una petición posterior
    (puede haber expirado o haber sido revocado)."""


class SecuronixNetworkError(SecuronixConnectorError):
    """No se pudo alcanzar el servidor Securonix (DNS, timeout, conexión
    rechazada, o error de TLS/certificado)."""


class SecuronixDataError(SecuronixConnectorError):
    """La operación es válida pero el incidente no existe, el estado
    solicitado no es válido, o el servidor rechazó la operación por una
    razón propia."""
