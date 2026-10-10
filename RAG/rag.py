"""
Ingesta de la base de conocimiento municipal: PDF → chunks → embeddings → PGVector.

Solo ingesta. La configuración de consulta (top_k) vive en tools/retrieval.py y
el par (embedding, colección) en vector_store.py, que comparten ambos lados.

Reindexa desde cero: borra la colección y la vuelve a cargar, para que correrlo
dos veces no duplique chunks.

Ejecutar desde la raíz del proyecto:
    python -m RAG.rag
"""

import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv

from vector_store import COLLECTION_NAME, get_vector_store, verificar_coleccion

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("DB_HOST")

CARPETA_DOCUMENTOS = Path(__file__).parent / "Base_de_Conocimiento"
TAMANO_CHUNK = 1000
SOLAPAMIENTO_CHUNK = 200


def verificar_configuracion() -> list[Path]:
    """Precondiciones antes de gastar una sola llamada de embeddings."""
    faltantes = [n for n, v in {"OPENAI_API_KEY": OPENAI_API_KEY, "DB_HOST": DB_HOST}.items() if not v]
    if faltantes:
        raise ValueError(f"Faltan variables en .env: {', '.join(faltantes)}")
    verificar_coleccion()
    pdfs = sorted(CARPETA_DOCUMENTOS.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No hay PDFs en {CARPETA_DOCUMENTOS}")
    return pdfs


if __name__ == "__main__":
    pdfs = verificar_configuracion()

    # 1. Document Loader
    documentos = []
    for pdf in pdfs:
        print(f"📄 Cargando {pdf.name}")
        documentos.extend(PyPDFLoader(str(pdf)).load())

    # 2. Splitting
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=TAMANO_CHUNK,
        chunk_overlap=SOLAPAMIENTO_CHUNK,
    )
    chunks = splitter.split_documents(documentos)
    print(f"✂️  {len(documentos)} páginas → {len(chunks)} chunks")

    # 3 y 4. Embeddings + Vector Store (reindexado limpio)
    vector_store = get_vector_store()
    vector_store.delete_collection()
    vector_store.create_collection()
    vector_store.add_documents(chunks)
    print(f"✅ {len(chunks)} chunks indexados en la colección '{COLLECTION_NAME}'")
