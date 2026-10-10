# Agente Municipal — LangChain v1 + FastAPI

Asistente virtual de atención ciudadana para una municipalidad (Alcaldía de
Girardota de ejemplo). Responde sobre trámites con el Manual de Trámites oficial
(RAG), busca información actual en internet (Tavily) y consulta la fecha y hora
reales. Recuerda cada conversación por `session_id`.

## Estructura

```
model_config/model.yaml        LLM (gpt-4.1) y límites de memoria
prompt/system_prompt.yaml      system prompt en YAML con tags XML
chat_history/
  postgres_store.py            pool + checkpointer de LangGraph (memoria del agente)
  conversation_log.py          log plano, una fila por mensaje (auditoría)
RAG/
  rag.py                       ingesta: PDF → chunks → embeddings → PGVector
  Base_de_Conocimiento/        PDFs de la municipalidad
tools/
  retrieval.py                 buscar_tramites_municipales (RAG)
  busqueda_internet.py         buscar_internet (Tavily)
  fecha_hora.py                obtener_fecha_hora
vector_store.py                fuente única de (embedding, colección)
migraciones_SQL/               SQL para Supabase, numerado e idempotente
agent.py                       orquestador: create_agent + middleware
app.py                         API FastAPI
.claude/skills/                skills usadas para construir este agente
```

## Puesta en marcha

```bash
# 1. Entorno
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Variables
cp .env.example .env        # rellena OPENAI, TAVILY y DB_* (Supabase, puerto 5432)

# 3. Base de datos: en el SQL Editor de Supabase
#    migraciones_SQL/001_extension_vector.sql y 002_conversation_log.sql

# 4. Ingesta de la base de conocimiento (una vez, o al cambiar los PDFs)
python -m RAG.rag

# 5. API
uvicorn app:app --reload --port 8000

# 6. Después del primer arranque: migraciones_SQL/003_rls.sql
```

## Uso

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "ciudadano-001", "mensaje": "¿Qué necesito para una licencia de construcción?"}'
```

```json
{
  "session_id": "ciudadano-001",
  "respuesta": "Para la licencia de construcción necesita...",
  "tools_usadas": ["buscar_tramites_municipales"]
}
```

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio |
| POST | `/chat` | Envía un mensaje; el `session_id` mantiene la memoria |
| GET | `/historial/{session_id}` | Conversación registrada en `conversation_log` |

Documentación interactiva en `http://localhost:8000/docs`.

## Memoria

- **Checkpointer** (`PostgresSaver`): estado del agente por `thread_id = session_id`.
- **Retención**: descarta mensajes con más de `retention_days` días.
- **Resumen** (`SummarizationMiddleware`): al pasar `token_limit` tokens resume lo
  antiguo y conserva los últimos `keep_messages` mensajes.
- **Log plano** (`conversation_log`): texto íntegro de cada mensaje para auditoría.
