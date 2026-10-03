# ResumeForge – Development Guide

> Step-by-step guide for setting up and working with the ResumeForge development environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Running Services](#running-services)
4. [Running Tests](#running-tests)
5. [Database Migrations](#database-migrations)
6. [Adding a New API Endpoint](#adding-a-new-api-endpoint)
7. [Adding a Background Task](#adding-a-background-task)
8. [Switching LLM Providers](#switching-llm-providers)
9. [Code Style & Conventions](#code-style--conventions)
10. [Git Workflow](#git-workflow)

---

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| Docker Desktop | 24+ | https://docs.docker.com/get-docker/ |
| Docker Compose | v2 (bundled with Docker Desktop) | Included |
| Python | 3.11+ | https://python.org |
| uv | latest | `pip install uv` |
| Node.js | 20+ | https://nodejs.org |
| npm | 10+ | Included with Node.js |
| GNU Make | 4+ | `winget install GnuWin32.Make` (Windows) |

Verify your setup:

```bash
docker --version          # Docker version 24+
docker compose version    # Docker Compose version v2+
python --version          # Python 3.11+
node --version            # v20+
make --version            # GNU Make 4+
```

---

## Initial Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/resumeforge.git
cd resumeforge
```

### 2. Configure environment variables

```bash
# Copy the example file
cp .env.example .env

# Edit the file — at minimum review:
#   SECRET_KEY          (generate with: openssl rand -hex 32)
#   LLM_PROVIDER        (use "ollama" for local dev)
#   POSTGRES_PASSWORD
```

### 3. Run first-time setup

```bash
make setup
```

This copies `.env.example` → `.env` (if not already present) and pulls the
required Docker images.

### 4. Start infrastructure

```bash
make up-infra
```

Starts PostgreSQL, Redis, and MailHog. Wait for them to be healthy:

```bash
make ps      # Check status — all should show "healthy"
```

### 5. Run database migrations

```bash
make migrate
```

### 6. Start all services

```bash
make up
```

### 7. Verify everything works

```bash
make health
# or open:
#   http://localhost:8000/docs  — FastAPI Swagger UI
#   http://localhost:3000       — Next.js frontend
#   http://localhost:8025       — MailHog Web UI
```

---

## Running Services

### Option A – Full Docker (recommended)

All services run inside Docker Compose. Changes to `apps/backend/` and
`apps/frontend/` are reflected immediately via bind-mount volumes.

```bash
make up              # Start everything
make logs            # Tail all logs
make logs-backend    # Tail only backend
make down            # Stop everything
```

### Option B – Local backend + Docker infra

Useful when you want faster iteration on the backend without rebuilding images.

```bash
# Start only infra
make up-infra

# Run backend locally (requires Python 3.11 + uv)
cd apps/backend
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Update DATABASE_URL in .env to use localhost instead of "postgres"
# DATABASE_URL=postgresql+asyncpg://resumeforge:...@localhost:5432/resumeforge

uvicorn app.main:app --reload --port 8000
```

### Option C – Local frontend + Docker infra + backend

```bash
# Start infra + backend in Docker
make up-infra
docker compose up -d backend

# Run frontend locally
cd apps/frontend
npm install
npm run dev
```

---

## Running Tests

### Backend tests

```bash
# Inside Docker
make backend-test

# Locally
cd apps/backend
pytest tests/ -v

# With coverage report
make test-backend
# Coverage HTML report: apps/backend/htmlcov/index.html
```

### Frontend linting / type-check

```bash
make frontend-lint
cd apps/frontend && npx tsc --noEmit
```

### All tests

```bash
make test
```

---

## Database Migrations

ResumeForge uses **Alembic** for database schema management.

### Apply all pending migrations

```bash
make migrate
# equivalent: docker compose exec backend alembic upgrade head
```

### Create a new migration

```bash
make migrate-create name="add_resume_status_column"
# Creates: apps/backend/alembic/versions/<timestamp>_add_resume_status_column.py
```

Always review the auto-generated migration file before applying it. Alembic's
`--autogenerate` flag compares ORM models to the current DB state.

### Rollback one step

```bash
docker compose exec backend alembic downgrade -1
```

### View migration history

```bash
docker compose exec backend alembic history --verbose
```

### Reset database (dev only)

```bash
make db-reset    # Drops & recreates the database
make migrate     # Re-applies all migrations
```

---

## Adding a New API Endpoint

Follow this pattern to add a new endpoint to the FastAPI backend:

### 1. Define the Pydantic schemas

```python
# apps/backend/app/schemas/my_feature.py
from pydantic import BaseModel

class MyFeatureCreate(BaseModel):
    name: str
    description: str | None = None

class MyFeatureResponse(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}
```

### 2. Define the SQLAlchemy model

```python
# apps/backend/app/models/my_feature.py
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class MyFeature(Base):
    __tablename__ = "my_features"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
```

### 3. Create the router

```python
# apps/backend/app/api/v1/endpoints/my_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.my_feature import MyFeatureCreate, MyFeatureResponse

router = APIRouter(prefix="/my-features", tags=["My Feature"])

@router.post("/", response_model=MyFeatureResponse, status_code=201)
async def create_my_feature(
    payload: MyFeatureCreate,
    db: AsyncSession = Depends(get_db),
):
    ...
```

### 4. Register the router

```python
# apps/backend/app/api/v1/router.py
from app.api.v1.endpoints.my_feature import router as my_feature_router
api_router.include_router(my_feature_router)
```

### 5. Create a migration

```bash
make migrate-create name="add_my_features_table"
make migrate
```

---

## Adding a Background Task

### 1. Define the task

```python
# apps/backend/app/workers/tasks/my_task.py
from app.workers.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def process_something(self, resource_id: int) -> dict:
    try:
        # ... do work ...
        return {"status": "complete", "resource_id": resource_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 2. Enqueue from the API

```python
from app.workers.tasks.my_task import process_something

# In a FastAPI endpoint:
task = process_something.delay(resource_id=42)
return {"task_id": task.id, "status": "queued"}
```

### 3. Poll task status

```python
from celery.result import AsyncResult

result = AsyncResult(task_id)
return {"status": result.status, "result": result.result}
```

---

## Switching LLM Providers

Change `LLM_PROVIDER` in your `.env` file and restart the backend:

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Then restart
docker compose restart backend celery_worker
```

| Provider | `.env` setting | Required keys |
|---|---|---|
| Ollama (local) | `LLM_PROVIDER=ollama` | None (must have Ollama running) |
| OpenAI | `LLM_PROVIDER=openai` | `OPENAI_API_KEY` |
| Gemini | `LLM_PROVIDER=gemini` | `GEMINI_API_KEY` |

For Ollama, ensure you have the model pulled locally:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

---

## Code Style & Conventions

### Python (Backend)

| Tool | Purpose | Config |
|---|---|---|
| **ruff** | Linting + formatting | `pyproject.toml` |
| **mypy** | Type checking | `pyproject.toml` |
| **pytest** | Testing | `pyproject.toml` |

```bash
# Lint
make backend-lint

# Format (auto-fix)
make backend-format
```

**Conventions:**
- Use `async/await` everywhere in the API layer — never block the event loop
- All public functions must have type annotations
- Use `structlog` for structured logging, not `print()`
- Keep routers thin — business logic belongs in service modules
- Use Pydantic v2 models for all request/response shapes

### TypeScript (Frontend)

| Tool | Purpose |
|---|---|
| **ESLint** | Linting |
| **Prettier** | Formatting |
| **TypeScript** | Type checking |

```bash
make frontend-lint
```

**Conventions:**
- Use the App Router (Next.js 14) — no Pages Router patterns
- Prefer Server Components; use Client Components only when needed
- All API calls go through a typed client generated from `@resumeforge/shared`
- Use `shadcn/ui` component primitives

---

## Git Workflow

### Branch Naming

```
feature/short-description        # New features
fix/short-description            # Bug fixes
chore/short-description          # Maintenance, deps, CI
docs/short-description           # Documentation only
refactor/short-description       # Code restructuring
```

### Commit Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add resume upload endpoint
fix: correct token expiry calculation
chore: upgrade pydantic to 2.7
docs: add API endpoint guide to development.md
refactor: extract LLM provider factory
test: add coverage for auth middleware
```

### Pull Request Process

1. Branch from `main`
2. Keep PRs focused — one logical change per PR
3. Ensure all tests pass locally (`make test`)
4. Request review from at least one team member
5. Squash-merge into `main`

### Protected Branches

- `main` — always deployable; requires PR + CI pass
- `production` — mirrors the production deployment

---

*See [architecture.md](architecture.md) for system design details.*
