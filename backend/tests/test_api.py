from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import seed_ready_doc
from app.database.session import SessionLocal
from app.models.entities import User
from app.rag import retriever


def _ids():
    db = SessionLocal()
    student = db.query(User).filter(User.role == "student").first()
    trainer = db.query(User).filter(User.role == "trainer").first()
    db.close()
    return student.id, trainer.id


def test_auth_and_roles():
    student_id, trainer_id = _ids()
    c = TestClient(app)
    users = c.get("/auth/users").json()
    assert len(users) >= 2
    me = c.get("/auth/me", headers={"X-User-Id": str(student_id)})
    assert me.status_code == 200
    forbidden = c.post(
        "/subjects",
        json={"name": "X", "code": "XX99"},
        headers={"X-User-Id": str(student_id)},
    )
    assert forbidden.status_code == 403


def test_subjects_crud_trainer():
    _, trainer_id = _ids()
    c = TestClient(app)
    h = {"X-User-Id": str(trainer_id)}
    listed = c.get("/subjects", headers=h)
    assert listed.status_code == 200
    assert len(listed.json()) >= 6
    sid = listed.json()[0]["id"]
    tree = c.get(f"/subjects/{sid}/tree", headers=h)
    assert tree.status_code == 200
    assert tree.json()["units"]
    renamed = c.put(f"/subjects/{sid}", json={"name": "Renamed Subject", "code": listed.json()[0]["code"]}, headers=h)
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Renamed Subject"


def test_quiz_submit_updates_competency(monkeypatch):
    student_id, trainer_id = _ids()
    sid, did, cid = seed_ready_doc()

    def fake_retrieve(query, subject_id, unit_id=None, topic_id=None, k=None):
        return [
            {
                "text": "Overfitting happens when a model memorizes training data.",
                "excerpt": "Overfitting happens when a model memorizes training data.",
                "similarity": 0.9,
                "document_id": did,
                "chunk_id": cid,
                "filename": "overfitting.md",
                "page_number": 1,
                "slide_number": None,
            }
        ]

    monkeypatch.setattr(retriever, "retrieve", fake_retrieve)
    import app.services.quiz_service as qs

    monkeypatch.setattr(qs, "retrieve", fake_retrieve)
    monkeypatch.setattr("app.rag.embedder.embed_texts", lambda texts: [[0.1] * 8 for _ in texts])
    monkeypatch.setattr("app.rag.embedder.cosine", lambda a, b: 0.9)

    c = TestClient(app)
    h = {"X-User-Id": str(student_id)}
    gen = c.post(
        "/quizzes/generate",
        json={"subject_id": sid, "num_questions": 3, "difficulty": "easy", "quiz_type": "regular"},
        headers=h,
    )
    assert gen.status_code == 200, gen.text
    quiz = gen.json()
    answers = [{"question_id": q["id"], "selected_option": 0} for q in quiz["questions"]]
    sub = c.post(f"/quizzes/{quiz['id']}/submit", json={"answers": answers, "attempt_id": quiz["attempt_id"]}, headers=h)
    assert sub.status_code == 200, sub.text
    body = sub.json()
    assert body["total_count"] == 3
    assert "competency_updates" in body
    prof = c.get(f"/students/{student_id}/competencies?subject_id={sid}", headers=h)
    assert prof.status_code == 200


def test_student_cannot_review_questions():
    student_id, _ = _ids()
    c = TestClient(app)
    r = c.get("/questions", headers={"X-User-Id": str(student_id)})
    assert r.status_code == 403
