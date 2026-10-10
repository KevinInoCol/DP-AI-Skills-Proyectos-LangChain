"""
Tool de fecha y hora actual por zona horaria. Solo stdlib (zoneinfo), sin APIs.

La zona por defecto es la del municipio (AGENT_TIMEZONE), así el agente nunca
supone la fecha: la consulta.
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain.tools import tool

from dotenv import load_dotenv

load_dotenv()

AGENT_TIMEZONE = os.getenv("AGENT_TIMEZONE", "America/Bogota")

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_hora_actual(zona: str = "") -> str:
    """Fecha y hora legibles en español. Si la zona no es válida usa la del agente."""
    zona = (zona or "").strip() or AGENT_TIMEZONE
    try:
        tz = ZoneInfo(zona)
    except Exception:
        zona, tz = AGENT_TIMEZONE, ZoneInfo(AGENT_TIMEZONE)
    ahora = datetime.now(tz)
    return (
        f"Zona horaria: {zona}\n"
        f"Fecha: {DIAS[ahora.weekday()]}, {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}\n"
        f"Hora: {ahora.strftime('%H:%M')}\n"
        f"ISO: {ahora.isoformat(timespec='seconds')}"
    )


@tool
def obtener_fecha_hora(zona_horaria: str = "") -> str:
    """Devuelve la fecha, el día de la semana y la hora ACTUALES.

    Úsala cuando el ciudadano pregunte qué día u hora es, o cuando necesites
    saber la fecha de hoy para calcular un plazo, una fecha de entrega o si
    una oficina está en horario de atención. Nunca supongas la fecha.

    Args:
        zona_horaria: zona IANA opcional (ej. 'Europe/Madrid'). Déjala vacía
            para usar la hora local del municipio.
    """
    print(f"   🕐 Fecha/hora: '{zona_horaria or AGENT_TIMEZONE}'")
    return fecha_hora_actual(zona_horaria)
