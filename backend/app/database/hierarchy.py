from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Competency, Subject, Topic, Unit


def competency_ids_for_subject(db: Session, subject_id: int) -> list[int]:
    rows = db.execute(
        select(Competency.id)
        .join(Topic, Competency.topic_id == Topic.id)
        .join(Unit, Topic.unit_id == Unit.id)
        .where(Unit.subject_id == subject_id)
    ).scalars().all()
    return list(rows)


def subject_tree(db: Session, subject: Subject) -> dict:
    units = db.scalars(
        select(Unit).where(Unit.subject_id == subject.id).order_by(Unit.order_index, Unit.id)
    ).all()
    unit_payload = []
    for unit in units:
        topics = db.scalars(
            select(Topic).where(Topic.unit_id == unit.id).order_by(Topic.order_index, Topic.id)
        ).all()
        topic_payload = []
        for topic in topics:
            comps = db.scalars(
                select(Competency).where(Competency.topic_id == topic.id).order_by(Competency.order_index, Competency.id)
            ).all()
            topic_payload.append(
                {
                    "id": topic.id,
                    "title": topic.title,
                    "description": topic.description,
                    "order_index": topic.order_index,
                    "competencies": [
                        {"id": c.id, "name": c.name, "description": c.description, "order_index": c.order_index}
                        for c in comps
                    ],
                }
            )
        unit_payload.append(
            {
                "id": unit.id,
                "title": unit.title,
                "description": unit.description,
                "order_index": unit.order_index,
                "topics": topic_payload,
            }
        )
    return {
        "id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "description": subject.description,
        "order_index": subject.order_index,
        "is_active": subject.is_active,
        "units": unit_payload,
    }
