"""
Tools del agente municipal. Un archivo por tool; cada uno exporta la función
imperativa (para tests) y la tool o su factory (para el agente).
"""

from tools.busqueda_internet import buscar_en_internet, get_busqueda_internet_tool
from tools.fecha_hora import fecha_hora_actual, obtener_fecha_hora
from tools.retrieval import buscar_tramites, get_retrieval_tool

__all__ = [
    "buscar_en_internet",
    "buscar_tramites",
    "fecha_hora_actual",
    "get_busqueda_internet_tool",
    "get_retrieval_tool",
    "obtener_fecha_hora",
]
