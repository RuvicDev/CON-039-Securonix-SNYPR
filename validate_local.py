"""Validación local del conector securonix_snypr: ejercita las 3 capacidades.

Requiere las env vars RUVIC_SECURONIX_SNYPR_* exportadas contra un tenant
de prueba real (no existe una versión de Securonix descargable/gratuita
para levantar localmente con Docker — a diferencia de SFTP/AD-LDAP, este
conector solo se puede probar contra un tenant real de un cliente).
"""

from ruvic_securonix_snypr_connector import SecuronixClient, setup_logging

setup_logging("INFO")
client = SecuronixClient()

print("== 1. Listar incidentes (sin filtro, para descubrir valores reales de status) ==")
incidentes = client.list_incidents(max_results=5)
print(f"  {len(incidentes)} incidente(s) encontrado(s)")
for i in incidentes[:3]:
    print(f"    {i}")

if incidentes:
    primer_id = incidentes[0].get("incidentId") or incidentes[0].get("id")
    if primer_id:
        print(f"== 2. Consultar el detalle del incidente {primer_id} ==")
        detalle = client.get_incident_detail(str(primer_id))
        print(f"  {detalle}")
    else:
        print("== 2. No se pudo extraer un incidentId del primer resultado — revisa la forma real de 'incidentes[0]' ==")
else:
    print("== 2. Se omite (no hay incidentes para consultar en este tenant) ==")

print(
    "\n== 3. update_incident_status NO se ejercita aquí automáticamente ==\n"
    "Cambiar el estado de un incidente real tiene efectos reales en el tenant. "
    "Pruébalo manualmente y con cuidado, ej.:\n\n"
    "  client.update_incident_status('ID_REAL', 'ESTADO_VALIDO_DEL_TENANT', comment='Prueba')\n"
)
