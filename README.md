# ResumeForge

> **AI-powered Resume Engineering SaaS** — Analyse, optimise, and tailor resumes to specific job descriptions using state-of-the-art language models and a Truth Guard system to prevent AI hallucinations.

[![Phase](https://img.shields.io/badge/Phase-3%20Complete-brightgreen)](#development-phases)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Node](https://img.shields.io/badge/Node.js-20%2B-green)](https://nodejs.org)
[![Tests](https://img.shields.io/badge/Tests-88%20passed-brightgreen)](#running-tests)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Overview

ResumeForge helps job seekers craft high-impact resumes by combining intelligent text analysis with actionable AI feedback. Users upload their resume and a target job description; the platform performs gap analysis, rewrites weak bullet points, calculates ATS keyword scores, and generates an optimised PDF — all powered by a configurable LLM backend (Ollama for local development, OpenAI or Gemini for production).

The system is built as a **full-stack monorepo**: a Next.js 14 frontend communicates with a FastAPI backend that delegates long-running AI tasks to Celery workers, persists structured data and vector embeddings in PostgreSQL + pgvector, and queues work through Redis.

---

## Architecture Overview

ResumeForge uses a microservice-style architecture running entirely in Docker Compose for local development. Key design decisions:

- **Provider-agnostic AI layer** — swap LLM backends by changing one env var
- **Async-first backend** — all I/O paths use `asyncio`; heavy work is offloaded to Celery
- **Vector search** — pgvector enables semantic similarity matching between resume sections and job requirements
- **Monorepo** — frontend, backend, and shared types live together with a clear package boundary

See [docs/architecture.md](docs/architecture.md) for the full system diagram and data flow documentation.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Frontend** | Next.js (App Router) | 14+ |
| **UI Components** | shadcn/ui + Tailwind CSS | latest |
| **Backend** | FastAPI + Pydantic v2 | 0.115+ / 2.x |
| **ORM & Migrations** | SQLAlchemy (async) + Alembic | 2.x |
| **Database** | PostgreSQL + pgvector | 16 |
| **Cache / Queue** | Redis | 7.4 |
| **Task Worker** | Celery | 5.x |
| **AI (local)** | Ollama (llama3.1:8b) | latest |
| **AI (production)** | OpenAI GPT-4o / Gemini 1.5 Pro | — |
| **Package Manager (Python)** | uv | latest |
| **Container Runtime** | Docker + Compose v2 | 24+ |

---

## Repository Structure

```
resumeforge/
├── apps/
│   ├── backend/            # FastAPI application (Python 3.11)
│   │   ├── app/
│   │   │   ├── api/        # Route handlers and dependencies
│   │   │   ├── models/     # SQLAlchemy ORM models
│   │   │   ├── schemas/    # Pydantic request/response schemas
│   │   │   ├── services/   # Business logic layer
│   │   │   └── workers/    # Celery tasks and app configuration
│   │   ├── alembic/        # Database migrations
│   │   ├── tests/          # pytest test suite
│   │   └── Dockerfile
│   └── frontend/           # Next.js 14 application (TypeScript)
│       ├── app/            # App Router pages and layouts
│       ├── components/     # Reusable React components
│       ├── lib/            # Utilities and API client
│       └── Dockerfile
├── packages/
│   └── shared/             # Shared TypeScript types (generated from OpenAPI)
├── docs/
│   ├── architecture.md     # System design and diagrams
│   └── development.md      # Developer setup guide (this context)
├── scripts/
│   ├── check_services.py   # Health-check script (stdlib only)
│   └── seed_db.py          # Database seed script
├── docker-compose.yml      # Production-ready service definitions
├── docker-compose.override.yml  # Dev overrides (Adminer, debug flags)
├── .env.example            # Template for all environment variables
├── Makefile                # Developer CLI (make help for full list)
└── README.md               # This file
```

---

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| **Docker Desktop** | 24+ | https://docs.docker.com/get-docker/ |
| **Docker Compose** | v2 (bundled) | Included with Docker Desktop |
| **Python** | 3.11+ | https://python.org |
| **uv** | latest | `pip install uv` |
| **Node.js** | 20+ | https://nodejs.org |
| **GNU Make** | 4+ | `winget install GnuWin32.Make` (Windows) |

---

## Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/dhruv282006/resumeforge.git
cd resumeforge

# Copy and edit environment variables
cp .env.example .env
```

Open `.env` and at minimum update:
- `SECRET_KEY` — generate with `openssl rand -hex 32`
- `POSTGRES_PASSWORD` — any secure password
- `LLM_PROVIDER` — use `ollama` for free local inference (no API key needed)

### 2. Start Infrastructure

```bash
# Pull images and start postgres, redis, mailhog
make up-infra

# Wait ~10 seconds, then verify:
make ps
```

All three services should show status `healthy`.

### 3. Run Migrations

```bash
make migrate
```

### 4. Start All Services

```bash
make up
```

### 5. Verify Health

```bash
make health
```

Or open these URLs in your browser:

| URL | What you'll see |
|---|---|
| http://localhost:3000 | Next.js frontend |
| http://localhost:8000/docs | FastAPI interactive API docs |
| http://localhost:8000/api/v1/health | `{"status": "ok"}` |
| http://localhost:8025 | MailHog — captured emails |

---

## Environment Variables

All environment variables are documented in [.env.example](.env.example). Copy it to `.env` and edit before running any services.

### Key Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | AI backend: `ollama` / `openai` / `gemini` | `ollama` |
| `DATABASE_URL` | Async PostgreSQL connection string | Points to `postgres` service |
| `REDIS_URL` | Redis connection string | Points to `redis` service |
| `SECRET_KEY` | JWT signing secret — **change in production!** | Placeholder |
| `OPENAI_API_KEY` | Required only when `LLM_PROVIDER=openai` | Empty |
| `GEMINI_API_KEY` | Required only when `LLM_PROVIDER=gemini` | Empty |
| `NEXT_PUBLIC_API_URL` | Browser-facing API base URL | `http://localhost:8000` |

> **Note on Docker networking:** Inside Docker Compose, services communicate using their service names as hostnames (e.g., `postgres`, `redis`). If you run services locally outside Docker, change these hostnames to `localhost` in your `.env`.

---

## Development Commands

Run `make help` to see all available targets. Key commands:

| Command | Description |
|---|---|
| `make setup` | First-time setup (copies .env.example, pulls images) |
| `make up` | Start all Docker services |
| `make up-infra` | Start infrastructure only (postgres, redis, mailhog) |
| `make down` | Stop all services |
| `make logs` | Tail logs for all services |
| `make logs-backend` | Tail backend logs |
| `make ps` | Show container status |
| `make migrate` | Run database migrations |
| `make migrate-create name="..."` | Create a new migration |
| `make test` | Run all tests |
| `make test-backend` | Run backend tests with coverage |
| `make backend-lint` | Run ruff linter |
| `make health` | Check all service health endpoints |
| `make clean` | Remove Python cache and build artifacts |

---

## Running Tests

```bash
# All tests
make test

# Backend only (with coverage)
make test-backend
# HTML report: apps/backend/htmlcov/index.html

# Verbose output
make test-verbose

# Frontend linting
make frontend-lint
```

---

## Services & Ports

| Service | Port | URL |
|---|---|---|
| **Frontend** (Next.js) | 3000 | http://localhost:3000 |
| **Backend** (FastAPI) | 8000 | http://localhost:8000 |
| **API Docs** (Swagger) | 8000 | http://localhost:8000/docs |
| **API Docs** (ReDoc) | 8000 | http://localhost:8000/redoc |
| **PostgreSQL** | 5432 | `postgresql://localhost:5432` |
| **Redis** | 6379 | `redis://localhost:6379` |
| **MailHog Web UI** | 8025 | http://localhost:8025 |
| **MailHog SMTP** | 1025 | `smtp://localhost:1025` |
| **Adminer** (dev only) | 8080 | http://localhost:8080 |

---

## Phase 0 Status

Phase 0 establishes the complete development infrastructure. The following has been completed:

- [x] Docker Compose configuration with all services
- [x] Development overrides (`docker-compose.override.yml`) with Adminer
- [x] Backend Dockerfile (Python 3.11 + uv)
- [x] Frontend Dockerfile (Node.js 20)
- [x] Environment variable template (`.env.example`)
- [x] Comprehensive `.gitignore`
- [x] `Makefile` with full developer CLI
- [x] `scripts/check_services.py` — stdlib health checker
- [x] `scripts/seed_db.py` — seed stub
- [x] `packages/shared/` — TypeScript shared types placeholder
- [x] `docs/architecture.md` — system design documentation
- [x] `docs/development.md` — developer guide

---

## Development Phases

| Phase | Focus | Status |
|---|---|---|
| **0** | Infrastructure & dev environment (Docker, FastAPI scaffold, Celery, Redis, pgvector) | ✅ Complete |
| **1** | Profile & Resume Core (User/Profile/Experience/Skill/Resume models, CRUD API, Alembic migrations) | ✅ Complete |
| **2** | Job Intelligence & Semantic Matching Engine (JD parsing, BM25 + semantic matching, explainable Match Score) | ✅ Complete |
| **3** | AI Resume Tailoring, Truth Guard & Version Intelligence (grounded suggestions, hallucination prevention, version diff) | ✅ Complete |
| **4** | Recruiter / Placement Cell portal, multi-tenant, bulk analysis | 🔜 Planned |
| **5** | Production hardening: observability, CI/CD, scaling, billing | 🔜 Planned |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Follow the conventions in [docs/development.md](docs/development.md)
4. Run `make test` and `make backend-lint` before committing
5. Submit a pull request with a clear description

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

---

## License

MIT © ResumeForge Contributors — see [LICENSE](LICENSE) for details.
