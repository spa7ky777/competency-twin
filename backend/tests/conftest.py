import json
import os
import tempfile
from pathlib import Path

tmp = tempfile.mkdtemp(prefix="ctwin-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp).as_posix()}/test.db"
os.environ["CHROMA_PATH"] = str(Path(tmp) / "chroma")
os.environ["UPLOAD_DIR"] = str(Path(tmp) / "uploads")
Path(os.environ["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["CHROMA_PATH"]).mkdir(parents=True, exist_ok=True)

from app.config import get_settings

get_settings.cache_clear()

from app.ai.ollama_service import OllamaService
from app.database.init_db import init_db
from app.database.seed import run_seed
from app.database.session import SessionLocal
from app.main import app
from app.models.entities import Document, DocumentChunk, Subject, User


class FakeOllama(OllamaService):
    def health_check(self):
        return {"ok": True, "reachable": True, "model_installed": True, "model": "fake", "status": "ok", "message": None}

    def _chat(self, prompt: str, json_mode: bool = False) -> str:
        if json_mode and "questions" in prompt.lower() or "JSON" in prompt:
            return json.dumps(
                {
                    "questions": [
                        {
                            "question": "What is overfitting?",
                            "options": [
                                "High training and low test performance",
                                "A clustering method",
                                "Always underfitting",
                                "A type of database",
                            ],
                            "correct_index": 0,
                            "explanation": "Overfitting memorizes training data.",
                            "difficulty": "easy",
                            "topic": "ML",
                            "competency": "Overfitting",
                            "source_label": "S1",
                        }
                    ]
                }
            )
        if "couldn't find" in prompt:
            return "I couldn't find this in the uploaded course material."
        return "Overfitting is when training accuracy is high but test accuracy is low [S1]."

    def generate_quiz(self, context_chunks, n, difficulty, topic, competency):
        qs = []
        for i in range(n):
            qs.append(
                {
                    "question": f"Question {i+1} about {topic}?",
                    "options": ["High train low test", "Always k-means", "A loss called clustering", "None needed here x"],
                    "correct_index": 0,
                    "explanation": "From excerpt.",
                    "difficulty": "easy",
                    "topic": topic,
                    "competency": competency,
                    "source_label": "S1",
                }
            )
        return qs

    def generate_answer(self, question, context_chunks, subject="", unit="", topic=""):
        if "not in material xyzzy" in question.lower() or "unicorn" in question.lower():
            return "I couldn't find this in the uploaded course material."
        return "Overfitting is high train / low test performance [S1]."


app.state.ollama = FakeOllama(get_settings())
init_db()
run_seed()


def seed_ready_doc():
    db = SessionLocal()
    sub = db.query(Subject).first()
    doc = Document(
        subject_id=sub.id,
        original_filename="overfitting.md",
        stored_filename="overfitting.md",
        file_type="md",
        file_size=100,
        status="ready",
        chunk_count=1,
    )
    db.add(doc)
    db.flush()
    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        text="Overfitting happens when a model memorizes training data and fails on new data.",
        char_count=80,
        chroma_id="c1",
    )
    db.add(chunk)
    db.commit()
    sid, did, cid = sub.id, doc.id, chunk.id
    db.close()
    return sid, did, cid
