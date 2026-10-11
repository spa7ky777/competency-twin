from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.hierarchy import competency_ids_for_subject
from app.database.session import get_db
from app.deps import get_current_user
from app.models.entities import CompetencyHistory, Quiz, QuizAttempt, Recommendation, Subject, User
from app.services.competency_service import learner_profile

router = APIRouter(prefix="/students", tags=["students"])


def _own(user: User, student_id: int):
    if user.role != "trainer" and user.id != student_id:
        raise AppError("FORBIDDEN", "You can only view your own data.", 403)


@router.get("/{student_id}/competencies")
def comps(student_id: int, subject_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _own(user, student_id)
    return learner_profile(db, student_id, subject_id)


@router.get("/{student_id}/recommendations")
def recs(student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _own(user, student_id)
    rows = db.scalars(
        select(Recommendation).where(Recommendation.user_id == student_id, Recommendation.is_dismissed.is_(False)).order_by(Recommendation.priority)
    ).all()
    out = []
    for r in rows:
        from app.models.entities import Competency, Document, DocumentChunk

        c = db.get(Competency, r.competency_id)
        doc = db.get(Document, r.document_id) if r.document_id else None
        chunk = db.get(DocumentChunk, r.chunk_id) if r.chunk_id else None
        out.append(
            {
                "id": r.id,
                "competency_id": r.competency_id,
                "competency_name": c.name if c else None,
                "reason_text": r.reason_text,
                "priority": r.priority,
                "document_id": r.document_id,
                "filename": doc.original_filename if doc else None,
                "chunk_preview": (chunk.text[:240] if chunk else None),
                "page_number": chunk.page_number if chunk else None,
            }
        )
    return out


@router.get("/{student_id}/progress")
def progress(student_id: int, competency_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _own(user, student_id)
    stmt = select(CompetencyHistory).where(CompetencyHistory.user_id == student_id).order_by(CompetencyHistory.recorded_at)
    if competency_id:
        stmt = stmt.where(CompetencyHistory.competency_id == competency_id)
    rows = db.scalars(stmt).all()
    return [
        {
            "competency_id": h.competency_id,
            "score_before": h.score_before,
            "score_after": h.score_after,
            "quiz_score_percent": h.quiz_score_percent,
            "recorded_at": h.recorded_at.isoformat() if h.recorded_at else None,
            "attempt_id": h.attempt_id,
        }
        for h in rows
    ]


@router.get("/{student_id}/attempts")
def attempts(student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _own(user, student_id)
    rows = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == student_id).order_by(QuizAttempt.id.desc())).all()
    out = []
    for a in rows:
        quiz = db.get(Quiz, a.quiz_id)
        out.append(
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "title": quiz.title if quiz else "",
                "quiz_type": quiz.quiz_type if quiz else "",
                "score_percent": a.score_percent,
                "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            }
        )
    return out
