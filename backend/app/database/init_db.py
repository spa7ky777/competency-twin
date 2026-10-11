from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import engine
from app.models import entities  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def reset_db(db: Session | None = None) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
