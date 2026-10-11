from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: int = 180
    ollama_temperature: float = 0.2
    database_url: str = "sqlite:///./competency_twin.db"
    chroma_path: str = str(ROOT / "chroma_data")
    upload_dir: str = str(ROOT / "uploads")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_upload_mb: int = 25
    allowed_extensions: str = "pdf,docx,pptx,txt,md"
    chunk_size: int = 800
    chunk_overlap: int = 120
    rag_top_k: int = 5
    rag_min_similarity: float = 0.25
    grounding_min_similarity: float = 0.35
    cors_origins: str = "http://localhost:5173"
    status_thresholds: str = "39,59,74,89"
    score_ema_weight: float = 0.6
    diagnostic_questions: int = 10
    weak_competency_threshold: float = 60
    exclude_unapproved_from_student_quizzes: bool = True
    llm_json_retries: int = 3
    quiz_gen_batch_size: int = 4
    targeted_quiz_questions: int = 8
    max_context_chars: int = 6000
    seed_path: str = str(ROOT / "data" / "seed" / "seed_subjects.json")
    demo_dir: str = str(ROOT / "data" / "demo")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_ext_set(self) -> set[str]:
        return {e.strip().lower().lstrip(".") for e in self.allowed_extensions.split(",") if e.strip()}

    @property
    def thresholds(self) -> list[int]:
        return [int(x.strip()) for x in self.status_thresholds.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
