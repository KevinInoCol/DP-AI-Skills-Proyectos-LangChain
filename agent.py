"""
Orquestador del Agente Municipal: ensambla modelo, prompt, tools y memoria.

Solo orquesta. Cada pieza vive en su carpeta:
    model_config/model.yaml     → LLM y límites de memoria
    prompt/system_prompt.yaml   → system prompt (YAML + tags XML)
    tools/                      → retrieval, búsqueda en internet, fecha y hora
    chat_history/               → checkpointer + log plano en Postgres
    vector_store.py             → embeddings + colección del RAG

Recursos pesados (LLM, vector store, Tavily, pool de Postgres) se inicializan
UNA vez con init_resources(). Ninguna tool depende de la sesión, así que el
agente también se construye una sola vez; la memoria se separa por thread_id.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, before_model
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from chat_history import get_checkpointer, log_mensaje
from tools import get_busqueda_internet_tool, get_retrieval_tool, obtener_fecha_hora
from vector_store import get_vector_store

BASE_DIR = Path(__file__).parent
RUTA_MODEL_CONFIG = BASE_DIR / "model_config" / "model.yaml"
RUTA_SYSTEM_PROMPT = BASE_DIR / "prompt" / "system_prompt.yaml"

# {messages} es el ÚNICO placeholder permitido: el middleware hace .format(messages=...)
PROMPT_DE_RESUMEN = """Eres un asistente que resume conversaciones de atención ciudadana
de una municipalidad. Este resumen reemplazará los mensajes antiguos, así que conserva
solo lo necesario para continuar la atención:

- Perfil del ciudadano: nombre si lo dio, si consulta como persona o empresa.
- Trámites consultados y qué información oficial ya recibió (requisitos, costos, plazos).
- Dudas pendientes o lo que quedó por responder.
- Compromisos o próximos pasos que se le indicaron.

Responde solo con el resumen, en español, sin texto adicional.

<messages>
{messages}
</messages>"""

_agent = None


def _cargar_yaml(ruta: Path) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _render_system_prompt(bot_name: str, municipio: str) -> str:
    prompt_cfg = _cargar_yaml(RUTA_SYSTEM_PROMPT)
    return (
        prompt_cfg["system_prompt"]
        .replace("{bot_name}", bot_name)
        .replace("{municipio}", municipio)
    )


def _es_resumen(mensaje) -> bool:
    return (mensaje.additional_kwargs or {}).get("lc_source") == "summarization"


def _crear_middleware_retencion(retention_days: int):
    """Descarta del estado los mensajes con más de retention_days días."""

    @before_model
    def descartar_vencidos(state, runtime):
        limite = datetime.now(timezone.utc) - timedelta(days=retention_days)
        mensajes = state["messages"]
        corte = None
        # Corta solo en frontera de mensaje humano: nunca deja un ToolMessage huérfano
        for i, m in enumerate(mensajes):
            if m.type != "human" or _es_resumen(m):
                continue
            ts = (m.additional_kwargs or {}).get("ts")
            # Sin ts = vigente: no borrar historial previo a esta lógica
            if ts is None or datetime.fromisoformat(ts) >= limite:
                corte = i
                break
        if corte is None or corte == 0:
            return None
        resumenes = [m for m in mensajes[:corte] if _es_resumen(m)]
        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *resumenes, *mensajes[corte:]]}

    return descartar_vencidos


def init_resources(bot_name: str, municipio: str) -> None:
    """Una vez al arrancar la app. Deja el agente listo como singleton del módulo."""
    global _agent

    cfg = _cargar_yaml(RUTA_MODEL_CONFIG)
    llm_cfg, mem_cfg = cfg["llm"], cfg["memory"]

    llm = init_chat_model(
        llm_cfg["model"],
        model_provider=llm_cfg["provider"],
        temperature=llm_cfg["temperature"],
    )

    tools = [
        get_retrieval_tool(get_vector_store()),
        get_busqueda_internet_tool(),
        obtener_fecha_hora,
    ]

    # Orden: retención → resumen (no gastar un resumen en mensajes por borrar)
    middleware = [
        _crear_middleware_retencion(mem_cfg["retention_days"]),
        SummarizationMiddleware(
            model=llm,
            trigger=("tokens", mem_cfg["token_limit"]),
            keep=("messages", mem_cfg["keep_messages"]),
            summary_prompt=PROMPT_DE_RESUMEN,
        ),
    ]

    _agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=_render_system_prompt(bot_name, municipio),
        checkpointer=get_checkpointer(),
        middleware=middleware,
    )


def _tools_del_turno(mensajes: list) -> list[str]:
    """Nombres de las tools invocadas desde el último mensaje humano."""
    inicio = max((i for i, m in enumerate(mensajes) if m.type == "human"), default=-1) + 1
    return [
        llamada["name"]
        for m in mensajes[inicio:]
        for llamada in getattr(m, "tool_calls", None) or []
    ]


def responder(session_id: str, mensaje: str) -> dict:
    """Procesa un mensaje del ciudadano y devuelve la respuesta del agente."""
    if _agent is None:
        raise RuntimeError("Agente no inicializado: llama a init_resources() al arrancar.")

    # Se registra ANTES de invocar: si el turno falla queda constancia de la pregunta
    log_mensaje(session_id, "user", mensaje)

    entrada = HumanMessage(
        content=mensaje,
        additional_kwargs={"ts": datetime.now(timezone.utc).isoformat()},
    )
    resultado = _agent.invoke(
        {"messages": [entrada]},
        {"configurable": {"thread_id": session_id}},
    )

    respuesta = resultado["messages"][-1].text
    tools_usadas = _tools_del_turno(resultado["messages"])
    log_mensaje(session_id, "assistant", respuesta, tools_usadas)
    return {"respuesta": respuesta, "tools_usadas": tools_usadas}
