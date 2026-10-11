from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_db
from app.deps import require_trainer
from app.models.entities import Competency, Document, LearnerCompetency, Question, Subject, User

router = APIRouter(prefix="/trainer/analytics", tags=["trainer"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    students = db.scalars(select(User).where(User.role == "student")).all()
    subjects = db.scalars(select(Subject)).all()
    docs = db.scalars(select(Document)).all()
    qstats = dict(db.execute(select(Question.review_status, func.count()).group_by(Question.review_status)).all())
    return {
        "student_count": len(students),
        "subject_count": len(subjects),
        "documents": [
            {"id": d.id, "filename": d.original_filename, "status": d.status, "subject_id": d.subject_id}
            for d in docs
        ],
        "question_stats": qstats,
        "subjects": [{"id": s.id, "name": s.name} for s in subjects],
        "students": [{"id": u.id, "name": u.name, "email": u.email} for u in students],
    }


@router.get("/weak-areas")
def weak_areas(db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    settings = get_settings()
    recs = db.scalars(select(LearnerCompetency)).all()
    counts: dict[int, int] = {}
    avgs: dict[int, list[float]] = {}
    for r in recs:
        avgs.setdefault(r.competency_id, []).append(r.current_score)
        if r.current_score < settings.weak_competency_threshold:
            counts[r.competency_id] = counts.get(r.competency_id, 0) + 1
    out = []
    for cid, n in sorted(counts.items(), key=lambda x: -x[1]):
        c = db.get(Competency, cid)
        scores = avgs[cid]
        out.append(
            {
                "competency_id": cid,
                "name": c.name if c else str(cid),
                "students_below_threshold": n,
                "class_average": sum(scores) / len(scores) if scores else None,
            }
        )
    return out


@router.get("/students/{student_id}")
def student_drill(student_id: int, db: Session = Depends(get_db), user: User = Depends(require_trainer)):
    from app.services.competency_service import learner_profile

    return learner_profile(db, student_id)
