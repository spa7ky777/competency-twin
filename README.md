# Competency Twin

A local-first adaptive learning app. Trainers add course material, and learners can ask grounded questions, complete quizzes, and track an evolving competency profile.

## Quick start (Windows)

Open two PowerShell windows at the repository root.

```powershell
.\scripts\start-backend.ps1
```

```powershell
.\scripts\start-frontend.ps1
```

Then open `http://localhost:5173`. The backend creates and seeds the local database at startup. For the AI tutor and generated quizzes, install Ollama, start it locally, and ensure the model in `.env` is available (the default is `qwen2.5:7b`).

## Configuration

Copy `.env.example` to `.env` to override defaults. `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `DATABASE_URL`, and `CORS_ORIGINS` control the backend. `VITE_API_BASE_URL` is optional and lets a separately hosted frontend target its API.

## Checks

From `backend`, run:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

From `frontend`, run:

```powershell
npm run build
```
