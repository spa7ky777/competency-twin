from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.session import get_db
from app.deps import get_current_user
from app.models.entities import Quiz, QuizAttempt, User
from app.services import quiz_service

router = APIRouter(tags=["quizzes"])


class GenerateIn(BaseModel):
    subject_id: int
    unit_id: int | None = None
    topic_id: int | None = None
    competency_id: int | None = None
    num_questions: int = 5
    difficulty: str = "medium"
    quiz_type: str = "regular"


class SubmitIn(BaseModel):
    answers: list[dict]
    attempt_id: int | None = None


@router.post("/quizzes/generate")
def generate(body: GenerateIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quiz = quiz_service.generate_quiz(
        db,
        request.app.state.ollama,
        subject_id=body.subject_id,
        user_id=user.id,
        num_questions=min(max(body.num_questions, 1), 15),
        difficulty=body.difficulty,
        quiz_type=body.quiz_type,
        unit_id=body.unit_id,
        topic_id=body.topic_id,
        competency_id=body.competency_id,
    )
    attempt = quiz_service.start_attempt(db, quiz.id, user.id)
    data = quiz_service.quiz_for_student(db, quiz, reveal=False)
    data["attempt_id"] = attempt.id
    return data


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise AppError("NOT_FOUND", "Quiz not found.", 404)
    attempt = quiz_service.start_attempt(db, quiz.id, user.id)
    data = quiz_service.quiz_for_student(db, quiz, reveal=False)
    data["attempt_id"] = attempt.id
    return data


@router.post("/quizzes/{quiz_id}/submit")
def submit(quiz_id: int, body: SubmitIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return quiz_service.submit_quiz(db, request.app.state.ollama, quiz_id, user.id, body.answers, body.attempt_id)


@router.get("/attempts/{attempt_id}")
def attempt(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    att = db.get(QuizAttempt, attempt_id)
    if not att or (att.user_id != user.id and user.role != "trainer"):
        raise AppError("NOT_FOUND", "Attempt not found.", 404)
    quiz = db.get(Quiz, att.quiz_id)
    review = quiz_service.quiz_for_student(db, quiz, reveal=True) if att.submitted_at else quiz_service.quiz_for_student(db, quiz, reveal=False)
    selected = {a.question_id: a.selected_option for a in att.answers}
    for q in review["questions"]:
        q["selected_option"] = selected.get(q["id"])
        if att.submitted_at:
            q["is_correct"] = q.get("selected_option") == q.get("correct_option")
    return {
        "id": att.id,
        "quiz_id": att.quiz_id,
        "score_percent": att.score_percent,
        "correct_count": att.correct_count,
        "total_count": att.total_count,
        "submitted_at": att.submitted_at.isoformat() if att.submitted_at else None,
        "review": review,
    }


class DiagIn(BaseModel):
    subject_id: int


@router.post("/diagnostic/start")
def diag_start(body: DiagIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quiz = quiz_service.diagnostic_start(db, request.app.state.ollama, user.id, body.subject_id)
    attempt = quiz_service.start_attempt(db, quiz.id, user.id)
    data = quiz_service.quiz_for_student(db, quiz, reveal=False)
    data["attempt_id"] = attempt.id
    return data


@router.post("/diagnostic/submit")
def diag_submit(body: SubmitIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not body.attempt_id:
        raise AppError("BAD_REQUEST", "attempt_id required")
    att = db.get(QuizAttempt, body.attempt_id)
    result = quiz_service.submit_quiz(db, request.app.state.ollama, att.quiz_id, user.id, body.answers, body.attempt_id)
    from app.services.competency_service import learner_profile

    quiz = db.get(Quiz, att.quiz_id)
    profile = learner_profile(db, user.id, quiz.subject_id)
    weak = profile["gaps"]["weak"]
    strong = profile["gaps"]["strong"]
    insights = []
    if strong:
        insights.append(f"Your strongest area is {strong[0]['name']}.")
    if weak:
        insights.append(f"Your largest competency gap is {weak[0]['name']}.")
    try:
        result["narrative"] = request.app.state.ollama.analyze_competency(
            {
                "strongest": strong[0]["name"] if strong else "n/a",
                "weakest": weak[0]["name"] if weak else "n/a",
                "coverage": profile.get("coverage"),
                "unassessed": len(profile["gaps"]["unassessed"]),
            }
        )
    except Exception:
        result["narrative"] = None
    result["insights"] = insights
    result["profile"] = profile
    return result


@router.post("/competencies/{comp_id}/targeted-quiz")
def targeted(comp_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quiz = quiz_service.targeted_quiz(db, request.app.state.ollama, user.id, comp_id)
    attempt = quiz_service.start_attempt(db, quiz.id, user.id)
    data = quiz_service.quiz_for_student(db, quiz, reveal=False)
    data["attempt_id"] = attempt.id
    return data
