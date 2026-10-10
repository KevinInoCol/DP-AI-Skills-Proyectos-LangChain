"""
Configuración del vector store: FUENTE ÚNICA del par (embedding model, colección).

La ingesta (RAG/rag.py) y la consulta (tools/retrieval.py) importan de aquí.
Si cambias el modelo de embeddings o la colección en un solo lado, el agente
responde "no encontré información" sobre documentos que sí están indexados.

Motor: PGVector (extensión pgvector) sobre el mismo Postgres de Supabase que
guarda la memoria. langchain-postgres crea sus tablas (langchain_pg_collection,
langchain_pg_embedding) y separa los documentos por collection_name.
"""

import os

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from dotenv import load_dotenv

from chat_history.postgres_store import build_database_url
from validacion_nombre_tenant_id import validar_qdrant

load_dotenv()

# Convención multi-tenant con guiones bajos (skill rag-tenant-collection-naming)
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION", "tenant_id_municipio_girardota")

EMBEDDING_MODEL = "text-embedding-3-small"


def verificar_coleccion() -> None:
    """Falla rápido si el nombre de la colección no cumple la convención."""
    validacion = validar_qdrant(COLLECTION_NAME)
    if not validacion.ok:
        raise ValueError(f"Nombre de colección inválido: {validacion.motivos}")


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def get_vector_store() -> PGVector:
    """Abre el vector store. Llamar UNA vez al arrancar, no por mensaje."""
    verificar_coleccion()
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=build_database_url(driver="postgresql+psycopg"),
        use_jsonb=True,
    )
