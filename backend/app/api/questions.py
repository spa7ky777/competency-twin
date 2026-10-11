import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.session import get_db
from app.deps import require_trainer
from app.models.entities import Document, Question, QuestionSource, User

router = APIRouter(tags=["questions"])


class QuestionPatch(BaseModel):
    question_text: str | None = None
    options: list[str] | None = None
    correct_option: int | None = None
    explanation: str | None = None
    difficulty: str | None = None
    review_status: str | None = None


def _q(q: Question, db: Session) -> dict:
    src = q.sources[0] if q.sources else None
    doc = db.get(Document, src.document_id) if src and src.document_id else None
    return {
        "id": q.id,
        "subject_id": q.subject_id,
        "topic_id": q.topic_id,
        "competency_id": q.competency_id,
        "question_text": q.question_text,
        "options": json.loads(q.options_json),
        "correct_option": q.correct_option,
        "explanation": q.explanation,
        "difficulty": q.difficulty,
        "review_status": q.review_status,
        "grounding_score": q.grounding_score,
        "generated_by_model": q.generated_by_model,
        "source": {
            "excerpt": src.source_excerpt if src else None,
            "filename": doc.original_filename if doc else None,
            "similarity": src.similarity if src else None,
        },
    }


@router.get("/questions")
def list_q(
    subject_id: int | None = None,
    topic_id: int | None = None,
    competency_id: int | None = None,
    review_status: str | None = None,
    difficulty: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_trainer),
):
    stmt = select(Question).order_by(Question.id.desc())
    if subject_id:
        stmt = stmt.where(Question.subject_id == subject_id)
    if topic_id:
        stmt = stmt.where(Question.topic_id == topic_id)
    if competency_id:
        stmt = stmt.where(Question.competency_id == competency_id)
    if review_status:
        stmt = stmt.where(Question.review_status == review_status)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    return [_q(q, db) for q in db.scalars(stmt.limit(200)).all()]


@router.put("/questions/{qid}")
def update_q(qid: int, body: QuestionPatch, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    q = db.get(Question, qid)
    if not q:
        raise AppError("NOT_FOUND", "Question not found.", 404)
    if body.question_text:
        q.question_text = body.question_text
    if body.options:
        q.options_json = json.dumps(body.options)
    if body.correct_option is not None:
        q.correct_option = body.correct_option
    if body.explanation is not None:
        q.explanation = body.explanation
    if body.difficulty:
        q.difficulty = body.difficulty
    if body.review_status:
        q.review_status = body.review_status
    db.commit()
    return _q(q, db)


@router.post("/questions/{qid}/approve")
def approve(qid: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    q = db.get(Question, qid)
    if not q:
        raise AppError("NOT_FOUND", "Question not found.", 404)
    q.review_status = "approved"
    db.commit()
    return _q(q, db)


@router.post("/questions/{qid}/reject")
def reject(qid: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    q = db.get(Question, qid)
    if not q:
        raise AppError("NOT_FOUND", "Question not found.", 404)
    q.review_status = "rejected"
    db.commit()
    return _q(q, db)


@router.delete("/questions/{qid}")
def delete_q(qid: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    q = db.get(Question, qid)
    if not q:
        raise AppError("NOT_FOUND", "Question not found.", 404)
    db.delete(q)
    db.commit()
    return {"ok": True}
