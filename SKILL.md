---
name: securonix-snypr
description: "Usa la librería ruvic_securonix_snypr_connector para consultar y gestionar incidentes en Securonix SNYPR (SIEM) - listar incidentes con filtros (list_incidents), consultar el detalle completo de un incidente (get_incident_detail), y actualizar su estado (update_incident_status). Úsala cuando el usuario pida revisar incidentes de seguridad, consultar violaciones, o cambiar el estado de un caso en Securonix. NO crea ni elimina incidentes, y no gestiona whitelists/watchlists."
triggers:
- securonix
- snypr
- siem
- incidente de seguridad
- violación
- alerta ueba
---

# Conector Securonix SNYPR (ruvic_securonix_snypr_connector)

Librería Python para consultar y gestionar incidentes en Securonix SNYPR, autenticada con usuario/contraseña (Securonix genera un token internamente, sin exponer OAuth ni Basic Auth). Está **preinstalada en el runtime** cuando el conector está configurado (si no, instálala con `pip install git+https://github.com/tu-org/conector-securonix-snypr.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de variables de entorno, disponibles cuando el conector `securonix_snypr` está configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_SECURONIX_SNYPR_BASE_URL` / `..._USERNAME` / `..._PASSWORD` | Siempre requeridas |
| `RUVIC_SECURONIX_SNYPR_TENANT_NAME` | (opcional) solo en instalaciones multi-tenant (MSSP) |
| `RUVIC_SECURONIX_SNYPR_TOKEN_VALIDITY_DAYS` | (opcional) default `365` |
| `RUVIC_SECURONIX_SNYPR_VERIFY_SSL` | (opcional) `true`/`false`, default `true` |
| `RUVIC_SECURONIX_SNYPR_REQUEST_TIMEOUT` | (opcional) segundos, default `30` |

Si estas variables NO existen, el conector no está configurado: no generes código que lo use; indica al usuario que lo configure en **Settings → Conectores**.

El código generado **NUNCA** usa nombres de variable con segmento de alias (`_DEFAULT_`, `_TEST_`, `_PRODUCCION_`, etc.) — siempre `{ENV_PREFIX}{CAMPO}` tal cual, sin importar cuántas instancias de este conector haya configuradas. Esto aplica salvo que dichos nombres aparezcan explícitamente en una sección autogenerada al final de este skill.

## Conexión (siempre igual)

```python
from ruvic_securonix_snypr_connector import SecuronixClient

client = SecuronixClient()  # lee RUVIC_SECURONIX_SNYPR_* del entorno automáticamente
```

La primera llamada a cualquier método genera el token automáticamente y lo renueva si expira. No es necesario llamar a un método de "login" por separado.

## Capacidad 1 — Listar incidentes

```python
incidentes = client.list_incidents(status="Open", priority="Critical")
for i in incidentes:
    print(i)
```

Los valores válidos de `status`/`priority` dependen de cómo esté configurado el workflow del tenant — si no los conoces, consulta primero sin filtro y observa qué valores aparecen en los resultados, en vez de inventarlos.

## Capacidad 2 — Consultar el detalle de un incidente

```python
detalle = client.get_incident_detail("12345")
print(detalle)
```

## Capacidad 3 — Actualizar el estado de un incidente

```python
client.update_incident_status("12345", "Closed", comment="Falso positivo confirmado")
```

Antes de cerrar o cambiar el estado de un incidente de seguridad, confirma la intención del usuario — es un cambio con implicaciones reales en el seguimiento de seguridad de la organización, no lo hagas por una instrucción ambigua.

## ⚠️ Nota sobre las rutas de API (importante para el agente)

Este conector expone las rutas de los 3 endpoints como configurables (`list_incidents_path`, `get_incident_path`, `update_status_path` en la configuración del conector), porque han variado entre versiones e instalaciones de Securonix. Si una operación falla con un error 404, es más probable que sea una ruta mal configurada para ese tenant específico que un error del código — informa esto al usuario en vez de asumir que el incidente no existe.

## Manejo de errores

```python
from ruvic_securonix_snypr_connector import (
    SecuronixAuthError, SecuronixNetworkError, SecuronixDataError,
)

try:
    client.list_incidents()
except SecuronixAuthError:
    print("Credenciales inválidas o token rechazado — revisa la configuración del conector")
except SecuronixNetworkError:
    print("No se pudo conectar a Securonix — revisa la red/VPN")
except SecuronixDataError as e:
    print(f"Error de datos: {e}")  # ej. incidente no encontrado, ruta de API mal configurada
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_SECURONIX_SNYPR_*` (el constructor de `SecuronixClient` ya lo hace).
2. Nunca imprimas `RUVIC_SECURONIX_SNYPR_PASSWORD` en logs ni en la salida.
3. No intentes crear ni eliminar incidentes, ni gestionar whitelists/watchlists: este conector no lo soporta.
4. No inventes valores de `status`/`priority` — confírmalos con una consulta sin filtro primero si no los conoces.
5. Antes de cambiar el estado de un incidente, confirma la intención del usuario — es una acción con impacto real en el seguimiento de seguridad.
