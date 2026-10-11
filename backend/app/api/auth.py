from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.deps import get_current_user, list_demo_users
from app.models.entities import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    user_id: int


@router.get("/users")
def users(db: Session = Depends(get_db)):
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in list_demo_users(db)]


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.get(User, body.user_id)
    if not user:
        from app.core.errors import AppError

        raise AppError("NOT_FOUND", "User not found.", 404)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "token": str(user.id)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
