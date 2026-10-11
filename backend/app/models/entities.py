from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def ts() -> Mapped[datetime]:
    return mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    units: Mapped[list["Unit"]] = relationship(back_populates="subject", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    subject: Mapped[Subject] = relationship(back_populates="units")
    topics: Mapped[list["Topic"]] = relationship(back_populates="unit", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    unit: Mapped[Unit] = relationship(back_populates="topics")
    competencies: Mapped[list["Competency"]] = relationship(back_populates="topic", cascade="all, delete-orphan")


class Competency(Base):
    __tablename__ = "competencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    topic: Mapped[Topic] = relationship(back_populates="competencies")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slide_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    competency_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    chroma_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    document: Mapped[Document] = relationship(back_populates="chunks")


class LearningResource(Base):
    __tablename__ = "learning_resources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competency_id: Mapped[int | None] = mapped_column(ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    resource_type: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text, default="")


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id", ondelete="SET NULL"), nullable=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True)
    competency_id: Mapped[int | None] = mapped_column(ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True, index=True)
    question_text: Mapped[str] = mapped_column(Text)
    options_json: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    review_status: Mapped[str] = mapped_column(String(20), default="needs_review", index=True)
    grounding_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    generated_by_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sources: Mapped[list["QuestionSource"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class QuestionSource(Base):
    __tablename__ = "question_sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_excerpt: Mapped[str] = mapped_column(Text, default="")
    similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    question: Mapped[Question] = relationship(back_populates="sources")


class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    quiz_type: Mapped[str] = mapped_column(String(20), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    unit_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    competency_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    items: Mapped[list["QuizQuestion"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    quiz: Mapped[Quiz] = relationship(back_populates="items")
    question: Mapped[Question] = relationship()


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    answers: Mapped[list["QuizAnswer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(Integer, index=True)
    selected_option: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    competency_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    attempt: Mapped[QuizAttempt] = relationship(back_populates="answers")


class LearnerCompetency(Base):
    __tablename__ = "learner_competencies"
    __table_args__ = (UniqueConstraint("user_id", "competency_id", name="uq_learner_comp"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), index=True)
    current_score: Mapped[float] = mapped_column(Float, default=0)
    previous_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    last_assessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    improvement_percent: Mapped[float] = mapped_column(Float, default=0)
    relative_improvement_percent: Mapped[float] = mapped_column(Float, default=0)


class CompetencyHistory(Base):
    __tablename__ = "competency_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), index=True)
    attempt_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    score_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_after: Mapped[float] = mapped_column(Float)
    quiz_score_percent: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), index=True)
    learning_resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason_text: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
