from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.session import get_db
from app.deps import get_current_user
from app.models.entities import Document, Subject, Topic, Unit, User
from app.rag.retriever import retrieve

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryIn(BaseModel):
    subject_id: int
    question: str
    unit_id: int | None = None
    topic_id: int | None = None


@router.post("/query")
def query(body: QueryIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subject = db.get(Subject, body.subject_id)
    if not subject:
        raise AppError("NOT_FOUND", "Subject not found.", 404)
    ready = db.scalar(select(Document).where(Document.subject_id == body.subject_id, Document.status == "ready"))
    if not ready:
        raise AppError("NO_MATERIAL", "This subject has no uploaded material yet. A trainer must upload documents or load demo material.")
    chunks = retrieve(body.question, body.subject_id, body.unit_id, body.topic_id)
    unit = db.get(Unit, body.unit_id) if body.unit_id else None
    topic = db.get(Topic, body.topic_id) if body.topic_id else None
    ollama = request.app.state.ollama
    if not chunks:
        answer = ollama.generate_answer(body.question, [], subject.name, unit.title if unit else "", topic.title if topic else "")
        return {"answer": answer, "sources": [], "grounded": False}
    answer = ollama.generate_answer(body.question, chunks, subject.name, unit.title if unit else "", topic.title if topic else "")
    grounded = "couldn't find this in the uploaded course material" not in answer.lower()
    sources = []
    for c in chunks:
        doc = db.get(Document, c.get("document_id")) if c.get("document_id") else None
        sources.append(
            {
                "document_id": c.get("document_id"),
                "filename": c.get("filename") or (doc.original_filename if doc else None),
                "page": c.get("page_number"),
                "slide": c.get("slide_number"),
                "chunk_id": c.get("chunk_id"),
                "excerpt": (c.get("text") or "")[:400],
                "similarity": c.get("similarity"),
            }
        )
    return {"answer": answer, "sources": sources, "grounded": grounded}
