"""
Tool de búsqueda en internet con Tavily (langchain-tavily).

Tool compartida: el cliente de Tavily se crea UNA vez en agent.init_resources().
Requiere TAVILY_API_KEY en el .env (se valida en el entrypoint).
"""

from langchain.tools import tool
from langchain_tavily import TavilySearch

MAX_RESULTADOS = 5
MAX_CARACTERES_POR_RESULTADO = 600


def buscar_en_internet(tavily: TavilySearch, consulta: str) -> str:
    """Búsqueda imperativa. Testeable sin el LLM. No lanza."""
    try:
        respuesta = tavily.invoke({"query": consulta})
    except Exception as e:
        print(f"❌ Error en Tavily: {e}")
        return "Error al buscar en internet. Responde con la información oficial disponible."

    resultados = respuesta.get("results", []) if isinstance(respuesta, dict) else []
    if not resultados:
        return "No se encontró información relevante en internet."

    bloques = []
    for i, r in enumerate(resultados, 1):
        contenido = (r.get("content") or "")[:MAX_CARACTERES_POR_RESULTADO]
        bloques.append(f"[{i}] {r.get('title', 'Sin título')}\n{contenido}\nFuente: {r.get('url', '')}")
    return "Resultados de internet (NO oficiales):\n\n" + "\n\n".join(bloques)


def get_busqueda_internet_tool():
    """Factory: crea el cliente de Tavily una sola vez y lo cierra en clausura."""
    tavily = TavilySearch(max_results=MAX_RESULTADOS, topic="general")

    @tool
    def buscar_internet(consulta: str) -> str:
        """Busca información pública ACTUAL en internet.

        Úsala para noticias, eventos, convocatorias, clima u otra información
        reciente del municipio, o cuando buscar_tramites_municipales no devolvió
        nada relevante. NO es fuente oficial de trámites: si la usas para un
        trámite, avisa al ciudadano que debe confirmarlo con la dependencia.
        No la uses para saludos ni para la fecha u hora.

        Args:
            consulta: búsqueda en lenguaje natural que incluya el nombre del
                municipio, ej. 'eventos culturales Girardota Antioquia octubre'.
        """
        print(f"   🌐 Internet: '{consulta}'")
        return buscar_en_internet(tavily, consulta)

    return buscar_internet
