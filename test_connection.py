"""Prueba de conexión estándar del conector securonix_snypr.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_SECURONIX_SNYPR_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Verifica la generación de token usando las env vars RUVIC_SECURONIX_SNYPR_*."""
    try:
        from ruvic_securonix_snypr_connector import (
            SecuronixAuthError,
            SecuronixClient,
            SecuronixDataError,
            SecuronixNetworkError,
        )
    except ImportError:
        return (
            False,
            "La librería ruvic-securonix-snypr-connector no está instalada. "
            "Instala con: pip install git+https://github.com/tu-org/"
            "conector-securonix-snypr.git#subdirectory=lib",
        )

    try:
        client = SecuronixClient()  # valida config y campos obligatorios
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except SecuronixAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except SecuronixNetworkError as exc:
        return False, f"Error de red: {exc}"
    except SecuronixDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return True, f"Conexión exitosa a {client.config.base_url}"


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)
