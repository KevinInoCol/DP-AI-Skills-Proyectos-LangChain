"""
Log plano de la conversación: una fila por mensaje, legible con SQL.

Complementa al checkpointer (postgres_store.py): sirve para reportes, QA y
auditoría, y conserva el texto original aunque la memoria del agente se resuma
o recorte. La tabla se crea con migraciones_SQL/001_conversation_log.sql.

Escritura fire-and-forget: un fallo aquí nunca impide responder al ciudadano.
"""

import json

from chat_history.postgres_store import get_pool

TABLA_LOG = "conversation_log"


def log_mensaje(
    session_id: str,
    rol: str,
    contenido: str,
    tools_usadas: list[str] | None = None,
) -> None:
    """Registra un mensaje (rol: 'user' o 'assistant'). Nunca lanza."""
    try:
        with get_pool().connection() as conn:
            conn.execute(
                f"INSERT INTO {TABLA_LOG} (session_id, role, content, tools_used) "
                "VALUES (%s, %s, %s, %s::jsonb)",
                (session_id, rol, contenido, json.dumps(tools_usadas or [])),
            )
    except Exception as e:
        print(f"⚠️ No se pudo registrar el mensaje en {TABLA_LOG}: {e}")


def obtener_historial(session_id: str, limite: int = 50) -> list[dict]:
    """Devuelve los últimos mensajes de una sesión, en orden cronológico."""
    with get_pool().connection() as conn:
        filas = conn.execute(
            f"SELECT role, content, tools_used, created_at FROM {TABLA_LOG} "
            "WHERE session_id = %s ORDER BY created_at DESC, id DESC LIMIT %s",
            (session_id, limite),
        ).fetchall()
    return [
        {"role": r[0], "content": r[1], "tools_used": r[2], "created_at": r[3].isoformat()}
        for r in reversed(filas)
    ]
