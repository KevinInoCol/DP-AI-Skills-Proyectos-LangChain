"""
Tool de Retrieval: consulta la base de conocimiento oficial de trámites (RAG).

Tool compartida: no depende de la sesión, así que se construye UNA vez en
agent.init_resources() sobre el vector store ya abierto.
"""

from langchain.tools import tool
from langchain_postgres import PGVector

TOP_K = 4


def buscar_tramites(vector_store: PGVector, consulta: str, top_k: int = TOP_K) -> str:
    """Búsqueda semántica imperativa. Testeable sin el LLM. No lanza."""
    try:
        resultados = vector_store.similarity_search(consulta, k=top_k)
    except Exception as e:
        print(f"❌ Error en retrieval: {e}")
        return ("Error al consultar la base de conocimiento. Indica al ciudadano "
                "que se comunique con la dependencia correspondiente.")

    if not resultados:
        return "No se encontró información sobre ese tema en el Manual de Trámites."

    bloques = []
    for i, doc in enumerate(resultados, 1):
        pagina = doc.metadata.get("page")
        ref = f" (página {pagina + 1})" if isinstance(pagina, int) else ""
        bloques.append(f"[{i}]{ref}\n{doc.page_content}")
    return "Información oficial del Manual de Trámites:\n\n" + "\n\n".join(bloques)


def get_retrieval_tool(vector_store: PGVector):
    """Factory: cierra el vector store en clausura. El LLM solo ve la consulta."""

    @tool
    def buscar_tramites_municipales(consulta: str) -> str:
        """Busca en el Manual de Trámites OFICIAL de la municipalidad. Es la
        fuente autoritativa sobre trámites administrativos.

        Úsala SIEMPRE que el ciudadano pregunte por un trámite: en qué consiste,
        requisitos y documentos, costos, cuentas bancarias o forma de pago,
        tiempos de respuesta, o qué secretaría o dependencia lo atiende.
        No la uses para noticias, eventos actuales ni para la fecha u hora.

        Args:
            consulta: palabras clave del trámite y de lo que se quiere saber,
                ej. 'requisitos licencia de construcción',
                'costo certificado de residencia', 'pago impuesto predial'.
        """
        print(f"   🔍 Retrieval: '{consulta}'")
        return buscar_tramites(vector_store, consulta)

    return buscar_tramites_municipales
