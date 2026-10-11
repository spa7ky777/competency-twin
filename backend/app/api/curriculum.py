from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.hierarchy import subject_tree
from app.database.session import get_db
from app.deps import get_current_user, require_trainer
from app.models.entities import Competency, Subject, Topic, Unit, User

router = APIRouter(tags=["curriculum"])


class SubjectIn(BaseModel):
    name: str
    code: str | None = None
    description: str = ""
    order_index: int = 0
    is_active: bool = True


class NamedIn(BaseModel):
    title: str | None = None
    name: str | None = None
    description: str = ""
    order_index: int = 0


@router.get("/subjects")
def list_subjects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Subject).order_by(Subject.order_index, Subject.id)).all()
    return [
        {"id": s.id, "name": s.name, "code": s.code, "description": s.description, "order_index": s.order_index, "is_active": s.is_active}
        for s in rows
    ]


@router.post("/subjects")
def create_subject(body: SubjectIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    code = body.code or body.name.upper().replace(" ", "_")[:32]
    if db.scalar(select(Subject).where(Subject.code == code)):
        raise AppError("CONFLICT", "Subject code already exists.", 409)
    s = Subject(name=body.name, code=code, description=body.description, order_index=body.order_index, is_active=body.is_active)
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "name": s.name, "code": s.code}


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.get(Subject, subject_id)
    if not s:
        raise AppError("NOT_FOUND", "Subject not found.", 404)
    return {"id": s.id, "name": s.name, "code": s.code, "description": s.description, "order_index": s.order_index, "is_active": s.is_active}


@router.put("/subjects/{subject_id}")
def update_subject(subject_id: int, body: SubjectIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    s = db.get(Subject, subject_id)
    if not s:
        raise AppError("NOT_FOUND", "Subject not found.", 404)
    s.name = body.name
    if body.code:
        s.code = body.code
    s.description = body.description
    s.order_index = body.order_index
    s.is_active = body.is_active
    db.commit()
    return {"id": s.id, "name": s.name, "code": s.code}


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    s = db.get(Subject, subject_id)
    if not s:
        raise AppError("NOT_FOUND", "Subject not found.", 404)
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.get("/subjects/{subject_id}/tree")
def tree(subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.get(Subject, subject_id)
    if not s:
        raise AppError("NOT_FOUND", "Subject not found.", 404)
    return subject_tree(db, s)


@router.get("/subjects/{subject_id}/units")
def units(subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Unit).where(Unit.subject_id == subject_id).order_by(Unit.order_index)).all()
    return [{"id": u.id, "title": u.title, "description": u.description, "order_index": u.order_index, "subject_id": u.subject_id} for u in rows]


@router.post("/subjects/{subject_id}/units")
def create_unit(subject_id: int, body: NamedIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    u = Unit(subject_id=subject_id, title=body.title or "Unit", description=body.description, order_index=body.order_index)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "title": u.title}


@router.put("/units/{unit_id}")
def update_unit(unit_id: int, body: NamedIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    u = db.get(Unit, unit_id)
    if not u:
        raise AppError("NOT_FOUND", "Unit not found.", 404)
    if body.title:
        u.title = body.title
    u.description = body.description
    u.order_index = body.order_index
    db.commit()
    return {"id": u.id, "title": u.title}


@router.delete("/units/{unit_id}")
def delete_unit(unit_id: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    u = db.get(Unit, unit_id)
    if not u:
        raise AppError("NOT_FOUND", "Unit not found.", 404)
    db.delete(u)
    db.commit()
    return {"ok": True}


@router.post("/units/{unit_id}/topics")
def create_topic(unit_id: int, body: NamedIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    t = Topic(unit_id=unit_id, title=body.title or "Topic", description=body.description, order_index=body.order_index)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "title": t.title}


@router.put("/topics/{topic_id}")
def update_topic(topic_id: int, body: NamedIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    t = db.get(Topic, topic_id)
    if not t:
        raise AppError("NOT_FOUND", "Topic not found.", 404)
    if body.title:
        t.title = body.title
    t.description = body.description
    t.order_index = body.order_index
    db.commit()
    return {"id": t.id, "title": t.title}


@router.get("/topics/{topic_id}")
def get_topic(topic_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Topic, topic_id)
    if not t:
        raise AppError("NOT_FOUND", "Topic not found.", 404)
    comps = db.scalars(select(Competency).where(Competency.topic_id == t.id).order_by(Competency.order_index)).all()
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "unit_id": t.unit_id,
        "competencies": [{"id": c.id, "name": c.name, "description": c.description} for c in comps],
    }


@router.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    t = db.get(Topic, topic_id)
    if not t:
        raise AppError("NOT_FOUND", "Topic not found.", 404)
    db.delete(t)
    db.commit()
    return {"ok": True}


@router.post("/topics/{topic_id}/competencies")
def create_comp(topic_id: int, body: NamedIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    c = Competency(topic_id=topic_id, name=body.name or body.title or "Competency", description=body.description, order_index=body.order_index)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}


@router.put("/competencies/{comp_id}")
def update_comp(comp_id: int, body: NamedIn, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    c = db.get(Competency, comp_id)
    if not c:
        raise AppError("NOT_FOUND", "Competency not found.", 404)
    c.name = body.name or body.title or c.name
    c.description = body.description
    c.order_index = body.order_index
    db.commit()
    return {"id": c.id, "name": c.name}


@router.delete("/competencies/{comp_id}")
def delete_comp(comp_id: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    c = db.get(Competency, comp_id)
    if not c:
        raise AppError("NOT_FOUND", "Competency not found.", 404)
    db.delete(c)
    db.commit()
    return {"ok": True}
