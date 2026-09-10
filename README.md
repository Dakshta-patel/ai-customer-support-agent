# AI Customer Support Agent

This project contains the initial structure for an AI customer support agent backend.

## Current status

This is a minimal FastAPI backend scaffold only. It does not include RAG, LLM integration, a database, a frontend, or any additional feature work yet.

## Project structure

- `backend/app/main.py` - FastAPI application entry point
- `backend/app/__init__.py` - Application package marker
- `backend/requirements.txt` - Python dependencies
- `backend/.env.example` - Example environment configuration
- `data/knowledge_base/` - Knowledge base directory placeholder
- `tests/` - Test directory placeholder

## Quick start

```bash
cd d:\ai-customer-support-agent
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r backend/requirements.txt
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/ to see the API response.

## Health check

```bash
curl http://localhost:8000/health
```
