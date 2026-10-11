import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.ollama_service import OllamaService
from app.competency.targeted import targeted_plan
from app.config import get_settings
from app.core.errors import AppError
from app.database.hierarchy import competency_ids_for_subject
from app.models.entities import (
    Competency,
    Document,
    DocumentChunk,
    LearnerCompetency,
    Question,
    QuestionSource,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
    Subject,
    Topic,
    Unit,
)
from app.rag import embedder
from app.rag.retriever import retrieve
from app.services.competency_service import apply_attempt_scores
from app.services.recommendation_service import regenerate_recommendations


def _chunks_for_scope(subject_id: int, unit_id: int | None, topic_id: int | None, query: str, k: int = 8) -> list[dict]:
    chunks = retrieve(query, subject_id, unit_id, topic_id, k=k)
    if not chunks:
        chunks = retrieve(query, subject_id, None, None, k=k)
    # diversity: prefer different document/chunk ids
    seen = set()
    diverse = []
    for c in chunks:
        key = c.get("chunk_id")
        if key in seen:
            continue
        seen.add(key)
        diverse.append(c)
    return diverse


def _persist_generated(db: Session, items: list[dict], context: list[dict], meta: dict, model: str) -> list[Question]:
    settings = get_settings()
    saved = []
    for item in items:
        label = (item.get("source_label") or "S1").upper().replace("S", "")
        try:
            idx = max(int(label) - 1, 0)
        except ValueError:
            idx = 0
        src = context[idx] if idx < len(context) else (context[0] if context else None)
        qtext = item["question"]
        options = item["options"]
        correct = item["correct_index"]
        pair = qtext + " " + options[correct]
        gscore = None
        status = "needs_review"
        if src and src.get("text"):
            try:
                vecs = embedder.embed_texts([pair, src["text"]])
                gscore = embedder.cosine(vecs[0], vecs[1])
            except Exception:
                gscore = src.get("similarity")
        if gscore is not None and gscore >= settings.grounding_min_similarity:
            status = "approved"
        q = Question(
            subject_id=meta["subject_id"],
            unit_id=meta.get("unit_id"),
            topic_id=meta.get("topic_id"),
            competency_id=meta.get("competency_id"),
            question_text=qtext,
            options_json=json.dumps(options),
            correct_option=correct,
            explanation=item.get("explanation") or "",
            difficulty=item.get("difficulty") or meta.get("difficulty") or "medium",
            review_status=status,
            grounding_score=gscore,
            generated_by_model=model,
        )
        db.add(q)
        db.flush()
        if src:
            db.add(
                QuestionSource(
                    question_id=q.id,
                    document_id=src.get("document_id"),
                    chunk_id=src.get("chunk_id"),
                    source_excerpt=(src.get("text") or "")[:800],
                    similarity=gscore,
                )
            )
        saved.append(q)
    return saved


def _bank_questions(db: Session, subject_id: int, competency_id: int | None, user_id: int | None, limit: int, difficulty: str | None) -> list[Question]:
    settings = get_settings()
    stmt = select(Question).where(Question.subject_id == subject_id)
    if settings.exclude_unapproved_from_student_quizzes:
        stmt = stmt.where(Question.review_status == "approved")
    if competency_id:
        stmt = stmt.where(Question.competency_id == competency_id)
    if difficulty and difficulty in ("easy", "medium", "hard"):
        stmt = stmt.where(Question.difficulty == difficulty)
    qs = list(db.scalars(stmt.order_by(Question.id.desc()).limit(limit * 3)))
    recent = set()
    if user_id:
        recent_rows = db.execute(
            select(QuizAnswer.question_id)
            .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
            .where(QuizAttempt.user_id == user_id)
        ).scalars().all()
        recent = set(recent_rows)
    out = [q for q in qs if q.id not in recent][:limit]
    return out


def generate_quiz(
    db: Session,
    ollama: OllamaService,
    *,
    subject_id: int,
    user_id: int,
    num_questions: int,
    difficulty: str,
    quiz_type: str,
    unit_id: int | None = None,
    topic_id: int | None = None,
    competency_id: int | None = None,
    title: str | None = None,
) -> Quiz:
    settings = get_settings()
    subject = db.get(Subject, subject_id)
    if not subject:
        raise AppError("NOT_FOUND", "Subject not found.", 404)
    ready = db.scalar(select(Document).where(Document.subject_id == subject_id, Document.status == "ready"))
    if not ready:
        raise AppError("NO_MATERIAL", "Upload learning material for this subject before generating quizzes or asking the tutor.")
    topic = db.get(Topic, topic_id) if topic_id else None
    comp = db.get(Competency, competency_id) if competency_id else None
    query = " ".join(filter(None, [subject.name, topic.title if topic else "", comp.name if comp else "", comp.description if comp else ""]))
    context = _chunks_for_scope(subject_id, unit_id, topic_id, query or subject.name)
    bank = _bank_questions(db, subject_id, competency_id, user_id, num_questions, None if "-" in difficulty else difficulty)
    needed = max(num_questions - len(bank), 0)
    generated: list[Question] = []
    batch = settings.quiz_gen_batch_size
    while needed > 0:
        n = min(batch, needed)
        raw = ollama.generate_quiz(context, n, difficulty.split("-")[0], topic.title if topic else subject.name, comp.name if comp else "")
        qs = _persist_generated(
            db,
            raw,
            context,
            {
                "subject_id": subject_id,
                "unit_id": unit_id,
                "topic_id": topic_id,
                "competency_id": competency_id,
                "difficulty": difficulty,
            },
            ollama.model,
        )
        generated.extend(qs)
        needed -= len(qs)
        if not qs:
            break
    all_q = bank + generated
    all_q = all_q[:num_questions]
    if not all_q:
        raise AppError("QUIZ_EMPTY", "Could not build a quiz. Try again after uploading material.")
    quiz = Quiz(
        title=title or f"{quiz_type.title()} quiz — {subject.name}",
        quiz_type=quiz_type,
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
        competency_id=competency_id,
        difficulty=difficulty,
        created_by=user_id,
    )
    db.add(quiz)
    db.flush()
    for i, q in enumerate(all_q):
        db.add(QuizQuestion(quiz_id=quiz.id, question_id=q.id, position=i))
    db.commit()
    db.refresh(quiz)
    return quiz


def start_attempt(db: Session, quiz_id: int, user_id: int) -> QuizAttempt:
    existing = db.scalar(
        select(QuizAttempt).where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == user_id,
            QuizAttempt.submitted_at.is_(None),
        )
    )
    if existing:
        return existing
    att = QuizAttempt(quiz_id=quiz_id, user_id=user_id)
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


def quiz_for_student(db: Session, quiz: Quiz, reveal: bool) -> dict:
    items = list(db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.position)))
    questions = []
    for item in items:
        q = db.get(Question, item.question_id)
        if not q:
            continue
        payload = {
            "id": q.id,
            "question_text": q.question_text,
            "options": json.loads(q.options_json),
            "difficulty": q.difficulty,
            "competency_id": q.competency_id,
            "position": item.position,
        }
        if reveal:
            payload["correct_option"] = q.correct_option
            payload["explanation"] = q.explanation
            src = q.sources[0] if q.sources else None
            payload["source"] = None
            if src:
                doc = db.get(Document, src.document_id) if src.document_id else None
                payload["source"] = {
                    "excerpt": src.source_excerpt,
                    "filename": doc.original_filename if doc else None,
                    "similarity": src.similarity,
                }
        questions.append(payload)
    return {
        "id": quiz.id,
        "title": quiz.title,
        "quiz_type": quiz.quiz_type,
        "subject_id": quiz.subject_id,
        "difficulty": quiz.difficulty,
        "competency_id": quiz.competency_id,
        "questions": questions,
    }


def submit_quiz(db: Session, ollama: OllamaService, quiz_id: int, user_id: int, answers: list[dict], attempt_id: int | None) -> dict:
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise AppError("NOT_FOUND", "Quiz not found.", 404)
    if attempt_id:
        attempt = db.get(QuizAttempt, attempt_id)
        if not attempt or attempt.user_id != user_id or attempt.quiz_id != quiz_id:
            raise AppError("NOT_FOUND", "Attempt not found.", 404)
    else:
        attempt = start_attempt(db, quiz_id, user_id)
    if attempt.submitted_at:
        raise AppError("ALREADY_SUBMITTED", "This attempt was already graded.")
    items = list(db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)))
    by_q = {a["question_id"]: a.get("selected_option") for a in answers}
    correct_n = 0
    stored = []
    for item in items:
        q = db.get(Question, item.question_id)
        selected = by_q.get(q.id)
        ok = selected is not None and selected == q.correct_option
        if ok:
            correct_n += 1
        ans = QuizAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            selected_option=selected,
            is_correct=ok,
            competency_id=q.competency_id,
        )
        db.add(ans)
        stored.append(ans)
    total = len(items)
    attempt.submitted_at = datetime.now(timezone.utc)
    attempt.correct_count = correct_n
    attempt.total_count = total
    attempt.score_percent = (correct_n / total * 100) if total else 0
    db.commit()
    updates = apply_attempt_scores(db, attempt, stored)
    regenerate_recommendations(db, user_id, ollama)
    review = quiz_for_student(db, quiz, reveal=True)
    for q in review["questions"]:
        q["selected_option"] = by_q.get(q["id"])
        q["is_correct"] = q.get("selected_option") == q.get("correct_option")
    return {
        "attempt_id": attempt.id,
        "score_percent": attempt.score_percent,
        "correct_count": correct_n,
        "total_count": total,
        "competency_updates": updates,
        "review": review,
    }


def diagnostic_start(db: Session, ollama: OllamaService, user_id: int, subject_id: int) -> Quiz:
    settings = get_settings()
    cids = competency_ids_for_subject(db, subject_id)
    if not cids:
        raise AppError("NO_COMPETENCIES", "This subject has no competencies.")
    n = settings.diagnostic_questions
    # round-robin: pick one question per competency cycling
    bank: list[Question] = []
    for i, cid in enumerate(cids):
        if len(bank) >= n:
            break
        found = _bank_questions(db, subject_id, cid, user_id, 1, None)
        bank.extend(found)
    quiz = generate_quiz(
        db,
        ollama,
        subject_id=subject_id,
        user_id=user_id,
        num_questions=n,
        difficulty="medium",
        quiz_type="diagnostic",
        title="Diagnostic assessment",
    )
    return quiz


def targeted_quiz(db: Session, ollama: OllamaService, user_id: int, competency_id: int) -> Quiz:
    settings = get_settings()
    comp = db.get(Competency, competency_id)
    if not comp:
        raise AppError("NOT_FOUND", "Competency not found.", 404)
    topic = db.get(Topic, comp.topic_id)
    unit = db.get(Unit, topic.unit_id)
    rec = db.scalar(
        select(LearnerCompetency).where(
            LearnerCompetency.user_id == user_id,
            LearnerCompetency.competency_id == competency_id,
        )
    )
    plan = targeted_plan(rec.current_score if rec else None, settings.targeted_quiz_questions)
    mix = plan["mix"]
    difficulty = mix[0]
    return generate_quiz(
        db,
        ollama,
        subject_id=unit.subject_id,
        user_id=user_id,
        num_questions=settings.targeted_quiz_questions,
        difficulty=difficulty,
        quiz_type="targeted",
        unit_id=unit.id,
        topic_id=topic.id,
        competency_id=competency_id,
        title=f"Practice: {comp.name}",
    )
