"""
Entrypoint FastAPI del Agente Municipal.

Capa de I/O: no sabe nada de LLMs, prompts ni storage. Solo conoce la API
pública de agent.py (init_resources, responder) y de chat_history/.

Endpoints:
    GET  /health                  → estado del servicio
    POST /chat                    → {session_id, mensaje} → respuesta del agente
    GET  /historial/{session_id}  → conversación registrada (log plano)

Ejecutar:
    uvicorn app:app --reload --port 8000
    Docs interactivas: http://localhost:8000/docs
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from dotenv import load_dotenv

import agent
from chat_history import close_pool, obtener_historial

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME", "Giri")
MUNICIPIO = os.getenv("MUNICIPIO", "Alcaldía de Girardota")

# Todas las que necesitan el agente y sus tools: se validan al arrancar, no en pleno request
VARIABLES_OBLIGATORIAS = [
    "OPENAI_API_KEY",
    "TAVILY_API_KEY",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
]


def verificar_configuracion() -> None:
    faltantes = [v for v in VARIABLES_OBLIGATORIAS if not os.getenv(v)]
    if faltantes:
        raise RuntimeError(f"Faltan variables en .env: {', '.join(faltantes)}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    verificar_configuracion()
    agent.init_resources(bot_name=BOT_NAME, municipio=MUNICIPIO)
    print(f"✅ Agente '{BOT_NAME}' listo para la {MUNICIPIO}")
    yield
    close_pool()


app = FastAPI(
    title="Agente Municipal",
    description="Asistente de atención ciudadana con LangChain: RAG de trámites, Tavily y fecha/hora.",
    version="1.0.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128, examples=["ciudadano-001"])
    mensaje: str = Field(..., min_length=1, max_length=4000,
                         examples=["¿Qué requisitos necesito para una licencia de construcción?"])


class ChatResponse(BaseModel):
    session_id: str
    respuesta: str
    tools_usadas: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agente": BOT_NAME}


# def (no async): FastAPI lo corre en un threadpool y no bloquea el event loop
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        resultado = agent.responder(req.session_id, req.mensaje)
    except Exception as e:
        print(f"❌ Error procesando sesión {req.session_id}: {e}")
        raise HTTPException(status_code=500, detail="El agente no pudo procesar el mensaje.")
    return ChatResponse(session_id=req.session_id, **resultado)


@app.get("/historial/{session_id}")
def historial(session_id: str, limite: int = 50) -> dict:
    return {"session_id": session_id, "mensajes": obtener_historial(session_id, limite)}
