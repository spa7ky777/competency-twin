# Competency Twin — start backend (run from repo root)
Set-Location $PSScriptRoot\..
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\Activate.ps1
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
