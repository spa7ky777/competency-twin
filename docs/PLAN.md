# Competency Twin — Architecture & Phases

## Stack (simple, local-first)

- **Frontend:** React 18 + Vite + TypeScript + Tailwind + React Router + TanStack Query + Recharts + Lucide + Sonner
- **Backend:** FastAPI + Pydantic v2 + SQLAlchemy 2 + SQLite (`init_db` + idempotent `seed.py`, no Alembic)
- **RAG:** PyMuPDF / python-docx / python-pptx → clean → RecursiveCharacterTextSplitter-style chunks → sentence-transformers singleton → ChromaDB persistent
- **LLM:** Ollama HTTP only via `OllamaService` (default `qwen2.5:7b`)
- **Auth:** Demo login; `X-User-Id` header; trainer-only routes

## Decisions

- Skip Alembic; `init_db()` creates tables; seed upserts by subject `code` and user email.
- Document processing as FastAPI `BackgroundTasks`.
- Quiz generation batches of 3–5 questions; reuse approved bank first.
- EMA: `weight = min(SCORE_EMA_WEIGHT * n/(n+3), 0.5)`; example 42 + 8/10 → ~59.5.
- Student quiz GET omits correct answers until submit.
- Windows: PowerShell scripts + `python`/`npm` commands; no bash-only scripts.

## Data flow (learner loop)

1. Trainer uploads docs → extract/clean/chunk/embed → SQLite chunks + Chroma.
2. Student RAG query → embed → retrieve → Ollama answer + sources.
3. Generate quiz from chunks (+ bank) → grounding score → persist.
4. Submit → grade → EMA competency scores + history → gaps → recommendations.
5. Targeted quiz on weak competency → same grading path.

## Phases

Follow master prompt phases 1–17: foundation → models/seed → CRUD → frontend kit → Ollama/JSON → ingestion → RAG UI → quizzes → player → competency/diagnostic → recs/targeted → dashboards → polish → tests/README.
