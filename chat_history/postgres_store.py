"""
Checkpointer de LangGraph sobre PostgreSQL (Supabase): la memoria del agente.

Guarda el estado de ejecución por thread_id (= session_id de la conversación).
Sus tablas (checkpoints, checkpoint_blobs, ...) son binarias y no se leen con
SQL; para auditar conversaciones está conversation_log.py.

Usa un ConnectionPool que valida la conexión antes de entregarla: una conexión
única cerrada por inactividad no se reconecta y el bot dejaría de responder.
"""

import os
from urllib.parse import quote_plus

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

POOL_MIN_SIZE = 1
POOL_MAX_SIZE = 10

_pool: ConnectionPool | None = None


def build_database_url(driver: str = "postgresql") -> str:
    """
    URL de conexión a partir de DB_*. La contraseña va escapada por si trae
    caracteres especiales. driver="postgresql+psycopg" para SQLAlchemy (PGVector).
    """
    password = quote_plus(DB_PASSWORD or "")
    return f"{driver}://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_pool() -> ConnectionPool:
    """Pool compartido por el checkpointer y el log plano. Se abre una sola vez."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            build_database_url(),
            min_size=POOL_MIN_SIZE,
            max_size=POOL_MAX_SIZE,
            # prepare_threshold=0: obligatorio detrás de un pooler (Supabase 6543)
            kwargs={"autocommit": True, "prepare_threshold": 0, "connect_timeout": 5},
            timeout=5,
            check=ConnectionPool.check_connection,
            open=True,
        )
    return _pool


def get_checkpointer() -> PostgresSaver:
    """Crea el checkpointer sobre el pool y sus tablas si no existen."""
    checkpointer = PostgresSaver(get_pool())
    checkpointer.setup()
    return checkpointer


def close_pool() -> None:
    """Cierra el pool al apagar la app."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
