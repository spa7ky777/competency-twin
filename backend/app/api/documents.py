from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.session import get_db
from app.deps import get_current_user, require_trainer
from app.models.entities import Document, DocumentChunk, User
from app.rag.pipeline import process_document
from app.services import document_service

router = APIRouter(tags=["documents"])


def _doc_out(d: Document) -> dict:
    return {
        "id": d.id,
        "subject_id": d.subject_id,
        "unit_id": d.unit_id,
        "topic_id": d.topic_id,
        "original_filename": d.original_filename,
        "file_type": d.file_type,
        "file_size": d.file_size,
        "status": d.status,
        "error_message": d.error_message,
        "page_count": d.page_count,
        "chunk_count": d.chunk_count,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.post("/documents/upload")
async def upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    subject_id: int = Form(...),
    unit_id: int | None = Form(None),
    topic_id: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_trainer),
):
    doc = document_service.save_upload(db, file, subject_id, user.id, unit_id, topic_id, background)
    return _doc_out(doc)


@router.get("/documents")
def list_docs(subject_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Document).order_by(Document.id.desc())
    if subject_id:
        stmt = stmt.where(Document.subject_id == subject_id)
    return [_doc_out(d) for d in db.scalars(stmt).all()]


@router.get("/documents/{doc_id}")
def get_doc(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    d = db.get(Document, doc_id)
    if not d:
        raise AppError("NOT_FOUND", "Document not found.", 404)
    chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == d.id).order_by(DocumentChunk.chunk_index)).all()
    out = _doc_out(d)
    out["chunks"] = [
        {
            "id": c.id,
            "chunk_index": c.chunk_index,
            "text": c.text[:500],
            "page_number": c.page_number,
            "slide_number": c.slide_number,
            "char_count": c.char_count,
        }
        for c in chunks
    ]
    return out


@router.delete("/documents/{doc_id}")
def del_doc(doc_id: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    document_service.delete_document(db, doc_id)
    return {"ok": True}


@router.post("/documents/{doc_id}/reprocess")
def reprocess(doc_id: int, background: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    d = db.get(Document, doc_id)
    if not d:
        raise AppError("NOT_FOUND", "Document not found.", 404)
    for c in list(d.chunks):
        db.delete(c)
    d.status = "pending"
    db.commit()
    background.add_task(process_document, d.id)
    return _doc_out(d)


class DemoIn(BaseModel):
    subject_id: int


@router.post("/demo/load")
def demo(body: DemoIn, background: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    docs = document_service.load_demo(db, body.subject_id, user.id, background)
    return {"documents": [_doc_out(d) for d in docs]}
