from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.session import get_db
from app.models.entities import User


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> User:
    if not x_user_id:
        raise AppError("UNAUTHENTICATED", "Select a demo user first.", 401)
    user = db.get(User, x_user_id)
    if not user:
        raise AppError("UNAUTHENTICATED", "Unknown user.", 401)
    return user


def require_trainer(user: User = Depends(get_current_user)) -> User:
    if user.role != "trainer":
        raise AppError("FORBIDDEN", "Trainer role required.", 403)
    return user


def list_demo_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))
