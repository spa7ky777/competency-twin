import argparse
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.models.entities import Competency, Subject, Topic, Unit, User


def upsert_user(db: Session, name: str, email: str, role: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.name = name
        user.role = role
        return user
    user = User(name=name, email=email, role=role)
    db.add(user)
    return user


def seed_from_json(db: Session, path: Path, reset_subjects: bool = False) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for u in data.get("users", []):
        upsert_user(db, u["name"], u["email"], u["role"])
    if reset_subjects:
        for sub in db.scalars(select(Subject)).all():
            db.delete(sub)
        db.flush()
    for s in data.get("subjects", []):
        sub = db.scalar(select(Subject).where(Subject.code == s["code"]))
        if not sub:
            sub = Subject(code=s["code"])
            db.add(sub)
        sub.name = s["name"]
        sub.description = s.get("description", "")
        sub.order_index = s.get("order_index", 0)
        sub.is_active = s.get("is_active", True)
        db.flush()
        existing_units = {u.order_index: u for u in sub.units}
        for u in s.get("units", []):
            unit = existing_units.get(u.get("order_index"))
            if not unit:
                unit = Unit(subject_id=sub.id)
                db.add(unit)
            unit.title = u["title"]
            unit.description = u.get("description", "")
            unit.order_index = u.get("order_index", 0)
            db.flush()
            existing_topics = {t.order_index: t for t in unit.topics}
            for t in u.get("topics", []):
                topic = existing_topics.get(t.get("order_index"))
                if not topic:
                    topic = Topic(unit_id=unit.id)
                    db.add(topic)
                topic.title = t["title"]
                topic.description = t.get("description", "")
                topic.order_index = t.get("order_index", 0)
                db.flush()
                existing_c = {c.order_index: c for c in topic.competencies}
                for c in t.get("competencies", []):
                    comp = existing_c.get(c.get("order_index"))
                    if not comp:
                        comp = Competency(topic_id=topic.id)
                        db.add(comp)
                    comp.name = c["name"]
                    comp.description = c.get("description", "")
                    comp.order_index = c.get("order_index", 0)
    db.commit()


def run_seed(reset_subjects: bool = False) -> None:
    init_db()
    settings = get_settings()
    path = Path(settings.seed_path)
    db = SessionLocal()
    try:
        seed_from_json(db, path, reset_subjects=reset_subjects)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset-subjects", action="store_true")
    args = parser.parse_args()
    run_seed(reset_subjects=args.reset_subjects)
