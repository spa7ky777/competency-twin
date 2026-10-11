import json
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.competency.gap_engine import rank_gaps
from app.competency.scoring import status_for, update_score
from app.config import get_settings
from app.database.hierarchy import competency_ids_for_subject
from app.models.entities import (
    Competency,
    CompetencyHistory,
    LearnerCompetency,
    QuizAnswer,
    QuizAttempt,
    Subject,
    Topic,
    Unit,
)


def apply_attempt_scores(db: Session, attempt: QuizAttempt, answers: list[QuizAnswer]) -> list[dict]:
    settings = get_settings()
    by_comp: dict[int, list[QuizAnswer]] = defaultdict(list)
    for a in answers:
        if a.competency_id:
            by_comp[a.competency_id].append(a)
    updates = []
    now = datetime.now(timezone.utc)
    for cid, items in by_comp.items():
        n = len(items)
        c = sum(1 for i in items if i.is_correct)
        quiz_pct = (c / n) * 100 if n else 0
        rec = db.scalar(
            select(LearnerCompetency).where(
                LearnerCompetency.user_id == attempt.user_id,
                LearnerCompetency.competency_id == cid,
            )
        )
        old = rec.current_score if rec else None
        new, _w = update_score(old, quiz_pct, n, settings.score_ema_weight)
        prev = rec.current_score if rec else None
        if not rec:
            rec = LearnerCompetency(user_id=attempt.user_id, competency_id=cid)
            db.add(rec)
        rec.previous_score = prev
        rec.current_score = new
        rec.attempts = (rec.attempts or 0) + 1
        rec.questions_attempted = (rec.questions_attempted or 0) + n
        rec.correct_answers = (rec.correct_answers or 0) + c
        rec.last_assessed_at = now
        rec.improvement_percent = new - (prev if prev is not None else new)
        rec.relative_improvement_percent = (
            ((new - prev) / prev * 100) if prev and prev > 0 else 0.0
        )
        db.add(
            CompetencyHistory(
                user_id=attempt.user_id,
                competency_id=cid,
                attempt_id=attempt.id,
                score_before=prev,
                score_after=new,
                quiz_score_percent=quiz_pct,
            )
        )
        updates.append(
            {
                "competency_id": cid,
                "quiz_percent": quiz_pct,
                "score_before": prev,
                "score_after": new,
                "delta": rec.improvement_percent,
                "status": status_for(new, settings.thresholds),
            }
        )
    db.commit()
    return updates


def learner_profile(db: Session, user_id: int, subject_id: int | None = None) -> dict:
    settings = get_settings()
    q = select(LearnerCompetency).where(LearnerCompetency.user_id == user_id)
    recs = list(db.scalars(q))
    items = []
    for rec in recs:
        comp = db.get(Competency, rec.competency_id)
        if not comp:
            continue
        topic = db.get(Topic, comp.topic_id)
        unit = db.get(Unit, topic.unit_id) if topic else None
        if subject_id and unit and unit.subject_id != subject_id:
            continue
        items.append(
            {
                "competency_id": rec.competency_id,
                "name": comp.name,
                "description": comp.description,
                "current_score": rec.current_score,
                "previous_score": rec.previous_score,
                "attempts": rec.attempts,
                "questions_attempted": rec.questions_attempted,
                "correct_answers": rec.correct_answers,
                "last_assessed_at": rec.last_assessed_at.isoformat() if rec.last_assessed_at else None,
                "improvement_percent": rec.improvement_percent,
                "relative_improvement_percent": rec.relative_improvement_percent,
                "status": status_for(rec.current_score, settings.thresholds),
                "subject_id": unit.subject_id if unit else None,
            }
        )
    assessed_ids = {i["competency_id"] for i in items}
    all_ids = competency_ids_for_subject(db, subject_id) if subject_id else []
    unassessed = []
    if subject_id:
        for cid in all_ids:
            if cid not in assessed_ids:
                c = db.get(Competency, cid)
                unassessed.append({"competency_id": cid, "name": c.name if c else str(cid), "current_score": None, "attempts": 0})
    gaps = rank_gaps(
        [
            {
                "competency_id": i["competency_id"],
                "name": i["name"],
                "current_score": i["current_score"],
                "attempts": i["attempts"],
                "last_assessed_at": datetime.fromisoformat(i["last_assessed_at"]) if i["last_assessed_at"] else None,
            }
            for i in items
        ]
        + unassessed,
        settings.weak_competency_threshold,
        settings.thresholds,
    )
    scores = [i["current_score"] for i in items]
    overall = sum(scores) / len(scores) if scores else None
    coverage = None
    if subject_id:
        coverage = {"assessed": len(items), "total": len(all_ids)}
    return {
        "items": items,
        "gaps": gaps,
        "overall": overall,
        "overall_status": status_for(overall, settings.thresholds) if overall is not None else None,
        "coverage": coverage,
    }
