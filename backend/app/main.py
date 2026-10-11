from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.ai.ollama_service import OllamaService
from app.api import auth, curriculum, documents, questions, quizzes, rag, students, trainer
from app.competency.status import status_payload
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.database.init_db import init_db
from app.database.seed import run_seed

settings = get_settings()
app = FastAPI(title="Competency Twin", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(auth.router)
app.include_router(curriculum.router)
app.include_router(documents.router)
app.include_router(rag.router)
app.include_router(quizzes.router)
app.include_router(questions.router)
app.include_router(students.router)
app.include_router(trainer.router)


@app.on_event("startup")
def startup():
    init_db()
    run_seed()
    app.state.ollama = OllamaService(settings)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/health/ai")
def health_ai(request: Request):
    return request.app.state.ollama.health_check()


@app.get("/config/competency")
def config_comp():
    return status_payload(settings.thresholds)
