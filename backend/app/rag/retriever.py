from app.config import get_settings
from app.rag.embedder import embed_texts
from app.rag.vector_store import query_vectors


def retrieve(query: str, subject_id: int, unit_id: int | None = None, topic_id: int | None = None, k: int | None = None) -> list[dict]:
    settings = get_settings()
    k = k or settings.rag_top_k
    qvec = embed_texts([query])[0]
    where: dict = {"subject_id": subject_id}
    if topic_id:
        where = {"$and": [{"subject_id": subject_id}, {"topic_id": topic_id}]}
    elif unit_id:
        where = {"$and": [{"subject_id": subject_id}, {"unit_id": unit_id}]}
    try:
        raw = query_vectors(qvec, n=max(k * 3, k), where=where)
    except Exception:
        raw = query_vectors(qvec, n=max(k * 3, k), where={"subject_id": subject_id})
    results = []
    ids = (raw.get("ids") or [[]])[0]
    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    dists = (raw.get("distances") or [[]])[0]
    for i, chroma_id in enumerate(ids):
        dist = dists[i] if i < len(dists) else 1.0
        sim = 1.0 - float(dist)
        if sim < settings.rag_min_similarity:
            continue
        meta = metas[i] if i < len(metas) else {}
        results.append(
            {
                "chroma_id": chroma_id,
                "text": docs[i] if i < len(docs) else "",
                "excerpt": docs[i] if i < len(docs) else "",
                "similarity": sim,
                "document_id": meta.get("document_id"),
                "chunk_id": meta.get("chunk_id"),
                "filename": meta.get("filename"),
                "page_number": meta.get("page_number"),
                "slide_number": meta.get("slide_number"),
                "subject_id": meta.get("subject_id"),
                "unit_id": meta.get("unit_id"),
                "topic_id": meta.get("topic_id"),
            }
        )
        if len(results) >= k:
            break
    return results
