import json
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import AppError
from app.core.security import sanitize_filename, stored_name, validate_upload
from app.models.entities import Document, Subject
from app.rag.pipeline import process_document, remove_document_vectors_and_chunks


def save_upload(
    db: Session,
    file: UploadFile,
    subject_id: int,
    user_id: int,
    unit_id: int | None,
    topic_id: int | None,
    background: BackgroundTasks,
) -> Document:
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    raw = file.file.read()
    ext = validate_upload(file.filename or "file.txt", len(raw), file.content_type)
    stored = stored_name(file.filename or f"file.{ext}")
    dest = Path(settings.upload_dir) / stored
    dest.write_bytes(raw)
    doc = Document(
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
        uploaded_by=user_id,
        original_filename=sanitize_filename(file.filename or stored),
        stored_filename=stored,
        file_type=ext,
        file_size=len(raw),
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    background.add_task(process_document, doc.id)
    return doc


def load_demo(db: Session, subject_id: int, user_id: int, background: BackgroundTasks) -> list[Document]:
    settings = get_settings()
    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppError("NOT_FOUND", "Subject not found.", 404)
    demo = Path(settings.demo_dir)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    created = []
    for path in sorted(demo.glob("*")):
        if path.suffix.lower().lstrip(".") not in settings.allowed_ext_set:
            continue
        stored = stored_name(path.name)
        copy2(path, Path(settings.upload_dir) / stored)
        doc = Document(
            subject_id=subject_id,
            uploaded_by=user_id,
            original_filename=sanitize_filename(path.name),
            stored_filename=stored,
            file_type=path.suffix.lower().lstrip("."),
            file_size=path.stat().st_size,
            status="pending",
        )
        db.add(doc)
        db.flush()
        created.append(doc)
    db.commit()
    for d in created:
        background.add_task(process_document, d.id)
        db.refresh(d)
    return created


def delete_document(db: Session, document_id: int) -> None:
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("NOT_FOUND", "Document not found.", 404)
    settings = get_settings()
    p = Path(settings.upload_dir) / doc.stored_filename
    if p.exists():
        p.unlink()
    remove_document_vectors_and_chunks(db, document_id)
