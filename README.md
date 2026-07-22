# conector-securonix-snypr

Conector Ruvic para Securonix SNYPR (SIEM): listar incidentes, consultar su detalle, y actualizar su estado.

## Capacidades

`list_incidents`, `get_incident_detail`, `update_incident_status`. No crea ni elimina incidentes, ni gestiona whitelists/watchlists/lookup tables — fuera de alcance a propósito.

## ⚠️ Nota honesta sobre las rutas de API

La documentación pública de Securonix confirma con certeza el **mecanismo de autenticación** (token generado a partir de usuario/contraseña vía `GET /ws/token/generate`), pero los nombres exactos de los endpoints de gestión de incidentes **han variado entre versiones** (6.3, 6.4, cloud vs on-prem) y no están completamente documentados en fuentes públicas accesibles.

Por eso las 4 rutas que usa este conector son **configurables** (ver variables de entorno abajo), con los valores por defecto más comúnmente documentados. **Antes de usar este conector contra un tenant real, verifica las rutas exactas** con el equipo de Securonix del cliente, o con el Postman collection que Securonix provee para pruebas — si no coinciden, ajusta las variables `*_PATH` sin necesitar ningún cambio de código.

## Instalación

Requiere **Python ≥ 3.10**.

```bash
pip install git+https://github.com/tu-org/conector-securonix-snypr.git#subdirectory=lib
```

Para desarrollo local (editable, en un venv limpio):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib
```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_SECURONIX_SNYPR_BASE_URL` | Sí | URL del tenant (ej. `https://miempresa.securonix.net`) |
| `RUVIC_SECURONIX_SNYPR_USERNAME` / `..._PASSWORD` | Sí | Credenciales del usuario de servicio |
| `RUVIC_SECURONIX_SNYPR_TENANT_NAME` | No | Solo en instalaciones multi-tenant (MSSP) |
| `RUVIC_SECURONIX_SNYPR_TOKEN_VALIDITY_DAYS` | No | Default `365` |
| `RUVIC_SECURONIX_SNYPR_VERIFY_SSL` | No | `true`/`false`, default `true` |
| `RUVIC_SECURONIX_SNYPR_TOKEN_PATH` | No | Default `/ws/token/generate` |
| `RUVIC_SECURONIX_SNYPR_LIST_INCIDENTS_PATH` | No | Default `/ws/incident/list` |
| `RUVIC_SECURONIX_SNYPR_GET_INCIDENT_PATH` | No | Default `/ws/incident/details` |
| `RUVIC_SECURONIX_SNYPR_UPDATE_STATUS_PATH` | No | Default `/ws/incident/actions` |
| `RUVIC_SECURONIX_SNYPR_REQUEST_TIMEOUT` | No | Segundos, default `30` |

## Permisos / prerrequisitos en Securonix

1. Pide al administrador de Securonix un **usuario de servicio dedicado**, con acceso al módulo de gestión de incidentes.
2. Permiso de **lectura** sobre incidentes (para `list_incidents`/`get_incident_detail`).
3. Permiso de **actualización de estado** solo si se va a usar `update_incident_status`.
4. Confirma con el administrador las **rutas exactas de la API REST** para la versión/instalación específica del tenant (ver nota de arriba).

## Cómo correr las pruebas locales

⚠️ A diferencia de SFTP/FTP o AD/LDAP, **no existe una versión de Securonix descargable para levantar con Docker** — este conector solo se puede probar contra un tenant real (de prueba o productivo) de un cliente.

```bash
export RUVIC_SECURONIX_SNYPR_BASE_URL=https://tenant-de-prueba.securonix.net
export RUVIC_SECURONIX_SNYPR_USERNAME=usuario_servicio
export RUVIC_SECURONIX_SNYPR_PASSWORD=xxxxxxxx

python test_connection.py
python validate_local.py
```

Prueba también el caso de error:

```bash
RUVIC_SECURONIX_SNYPR_PASSWORD=incorrecta python test_connection.py
# FALLO: Autenticación fallida: ...
```

## Limitaciones conocidas

- No crea ni elimina incidentes.
- No gestiona whitelists, watchlists, ni lookup tables (Securonix expone estas capacidades, pero quedaron fuera de alcance).
- No implementa "run activity query" (consultas Solr contra el log de eventos) — solo gestión de incidentes.
- Las rutas de API son configurables porque no se pudieron confirmar con certeza absoluta contra todas las versiones de Securonix — ver la nota de arriba.
- Nunca se ha probado contra un tenant Securonix real (pendiente hasta tener acceso a uno).

## Notas de integración

- El paquete pip es `ruvic-securonix-snypr-connector`; el import name es `ruvic_securonix_snypr_connector`.
- Única dependencia externa: `requests`.
- Ver `SKILL.md` para los ejemplos de uso que consume el agente.
