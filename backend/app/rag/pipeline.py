from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import AppError
from app.models.entities import Document, DocumentChunk, LearningResource
from app.rag.chunker import chunk_pages
from app.rag.cleaner import clean_text
from app.rag.embedder import embed_texts
from app.rag.extractors import extract_file
from app.rag.vector_store import delete_document_vectors, upsert_chunks
from app.database.session import SessionLocal


def process_document(document_id: int) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return
        doc.status = "processing"
        db.commit()
        path = Path(settings.upload_dir) / doc.stored_filename
        pages = extract_file(path, doc.file_type)
        for p in pages:
            p["text"] = clean_text(p["text"])
        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise AppError("NO_TEXT", "No extractable text found in this file.")
        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)
        chroma_ids = []
        for i, c in enumerate(chunks):
            row = DocumentChunk(
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                text=c["text"],
                page_number=c["page_number"],
                slide_number=c["slide_number"],
                topic_id=doc.topic_id,
                char_count=c["char_count"],
            )
            db.add(row)
            db.flush()
            cid = f"doc{doc.id}_chunk{row.id}"
            row.chroma_id = cid
            chroma_ids.append(cid)
            db.add(
                LearningResource(
                    competency_id=None,
                    topic_id=doc.topic_id,
                    document_id=doc.id,
                    chunk_id=row.id,
                    title=f"{doc.original_filename} chunk {i+1}",
                    resource_type="chunk",
                    description=(c["text"][:180] + "...") if len(c["text"]) > 180 else c["text"],
                )
            )
        metas = []
        for i, c in enumerate(chunks):
            metas.append(
                {
                    "document_id": doc.id,
                    "chunk_id": int(chroma_ids[i].split("chunk")[-1]),
                    "subject_id": doc.subject_id,
                    "unit_id": doc.unit_id or 0,
                    "topic_id": doc.topic_id or 0,
                    "filename": doc.original_filename,
                    "page_number": c["page_number"] or 0,
                    "slide_number": c["slide_number"] or 0,
                }
            )
        upsert_chunks(chroma_ids, embeddings, texts, metas)
        doc.chunk_count = len(chunks)
        doc.page_count = max((p.get("page_number") or p.get("slide_number") or 0) for p in pages) or len(pages)
        doc.status = "ready"
        doc.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc:
            doc.status = "failed"
            doc.error_message = str(getattr(exc, "message", exc))
            db.commit()
    finally:
        db.close()


def remove_document_vectors_and_chunks(db: Session, document_id: int) -> None:
    delete_document_vectors(document_id)
    doc = db.get(Document, document_id)
    if doc:
        db.delete(doc)
        db.commit()
