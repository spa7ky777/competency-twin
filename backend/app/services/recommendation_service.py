import json
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.ollama_service import OllamaService
from app.competency.scoring import status_for
from app.config import get_settings
from app.core.errors import AppError
from app.models.entities import Competency, Document, DocumentChunk, LearnerCompetency, Recommendation, Topic
from app.rag.retriever import retrieve


def regenerate_recommendations(db: Session, user_id: int, ollama: OllamaService | None = None) -> list[Recommendation]:
    settings = get_settings()
    existing = list(db.scalars(select(Recommendation).where(Recommendation.user_id == user_id, Recommendation.is_dismissed.is_(False))))
    for r in existing:
        db.delete(r)
    recs = list(db.scalars(select(LearnerCompetency).where(LearnerCompetency.user_id == user_id)))
    created = []
    priority = 0
    for rec in recs:
        if rec.current_score >= settings.weak_competency_threshold:
            continue
        comp = db.get(Competency, rec.competency_id)
        if not comp:
            continue
        status = status_for(rec.current_score, settings.thresholds)
        reason = f"Recommended because your {comp.name} competency is currently {rec.current_score:.0f}% ({status})."
        if ollama:
            try:
                extra = ollama._chat  # only through generate path
                from app.ai import prompts

                reason = ollama._chat(prompts.RECOMMENDATION.format(reason=reason)) or reason
            except Exception:
                pass
        topic = db.get(Topic, comp.topic_id)
        unit_id = topic.unit_id if topic else None
        subject_id = None
        if topic:
            from app.models.entities import Unit

            unit = db.get(Unit, topic.unit_id)
            subject_id = unit.subject_id if unit else None
        chunks = []
        if subject_id:
            try:
                chunks = retrieve(f"{comp.name} {comp.description}", subject_id, None, topic.id if topic else None, k=3)
            except Exception:
                chunks = []
        chunk = chunks[0] if chunks else None
        row = Recommendation(
            user_id=user_id,
            competency_id=comp.id,
            document_id=chunk.get("document_id") if chunk else None,
            chunk_id=chunk.get("chunk_id") if chunk else None,
            reason_text=reason.strip(),
            priority=priority,
        )
        db.add(row)
        created.append(row)
        priority += 1
    db.commit()
    return created
