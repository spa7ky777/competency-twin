from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

_client = None


def get_collection():
    global _client
    settings = get_settings()
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client.get_or_create_collection(name="course_chunks", metadata={"hnsw:space": "cosine"})


def upsert_chunks(ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> None:
    get_collection().upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def delete_document_vectors(document_id: int) -> None:
    col = get_collection()
    try:
        col.delete(where={"document_id": document_id})
    except Exception:
        pass


def query_vectors(embedding: list[float], n: int, where: dict | None = None) -> dict:
    col = get_collection()
    kwargs = {"query_embeddings": [embedding], "n_results": n}
    if where:
        kwargs["where"] = where
    return col.query(**kwargs)
