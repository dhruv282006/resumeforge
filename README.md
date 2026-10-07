# ResumeForge

> **AI-Powered Resume Engineering & Job Matching Platform** — Grounded candidate profiling, explainable semantic matching, zero-hallucination resume tailoring with Truth Guard 2.0, and end-to-end application tracking.

[![Status](https://img.shields.io/badge/Status-Phases%200--4%20Complete-emerald)](#features)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-91%2F91%20Passing-brightgreen)](#testing--quality-assurance)
[![Frontend Build](https://img.shields.io/badge/Frontend%20Build-15%2F15%20Routes%20Passing-brightgreen)](#testing--quality-assurance)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20App%20Router-black)](apps/frontend)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20Async-teal)](apps/backend)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%2016%20%2B%20pgvector-blue)](https://github.com/pgvector/pgvector)
[![AI Engine](https://img.shields.io/badge/AI%20Engine-Gemini%202.5%20%2F%20Ollama-purple)](https://ai.google.dev/)
[![Truth Guard](https://img.shields.io/badge/Truth%20Guard-2.0%20Zero--Hallucination-orange)](#truth-guard-20-engine)
[![OS Support](https://img.shields.io/badge/Platform-Windows%20Native%20%2B%20Docker-blueviolet)](#local-development-windows-11-native)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Table of Contents

- [Overview & Philosophy](#overview--philosophy)
- [System Architecture & Workflow](#system-architecture--workflow)
- [Core Features](#core-features)
  - [1. First Launch & Guided Onboarding](#1-first-launch--guided-onboarding)
  - [2. Multi-Tenant Authentication & Security](#2-multi-tenant-authentication--security)
  - [3. Master Career Profile](#3-master-career-profile)
  - [4. Resume Version Control](#4-resume-version-control)
  - [5. Job Intelligence & NLP Extraction](#5-job-intelligence--nlp-extraction)
  - [6. Explainable Semantic Matching](#6-explainable-semantic-matching)
  - [7. Truth Guard 2.0 & AI Tailoring](#7-truth-guard-20--ai-tailoring)
  - [8. Applications Pipeline Tracker](#8-applications-pipeline-tracker)
  - [9. Responsive Design & Mobile Navigation](#9-responsive-design--mobile-navigation)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Local Development (Windows 11 Native)](#local-development-windows-11-native)
- [Docker Alternative (Containerized)](#docker-alternative-containerized)
- [Environment Variables](#environment-variables)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [License](#license)

---

## Overview & Philosophy

Traditional AI resume tools fabricate fake metrics, invent technologies candidates have never touched, and output generic buzzword-stuffed paragraphs that immediately collapse under technical interview scrutiny.

**ResumeForge is built on a non-negotiable architectural rule:**
> **Zero Hallucination.** Every claim, metric, and skill suggested on a tailored resume must be strictly grounded in verified facts from the candidate's Master Career Profile.

### The Consumer-Centric Mental Model

ResumeForge follows an intuitive, transparent workflow designed for students and job seekers:

```
[Candidate Master Profile]  ── (Single Source of Truth)
           │
           ├────────────────────────────┐
           ▼                            ▼
[Target Job Description]      [Resume Version v1.0]
           │                            │
           └────────────┬───────────────┘
                        ▼
            [Semantic Vector Match]
         (PostgreSQL 16 + pgvector)
                        │
                        ▼
          [AI Tailoring & Truth Guard 2.0]
      (Gemini 2.5 Flash / Ollama Fallback)
         - Blocks fabricated claims
         - Verifies evidence against Master Profile
                        │
                        ▼
         [Tailored Snapshot v1.1 + Diff]
      - Line-by-line diff (+added, -removed)
      - Before vs. After score comparison
                        │
                        ▼
         [Job Application Tracker]
    (Applied -> Screening -> Interviewing -> Offer)
```

---

## Core Features

### 1. First Launch & Guided Onboarding
- **Welcome Landing Page (`/`)**: Clear value proposition, zero-hallucination explanation, and direct authentication entrypoints. Automatically redirects authenticated candidates to the dashboard.
- **5-Step Onboarding Wizard (`/onboarding`)**: Seamlessly takes new candidates through:
  1. *Basic Details & Headline* (Full Name, Target Role, Location, Phone, Summary)
  2. *Education* (Institution, Degree, Field of Study, Graduation Year, GPA)
  3. *Verified Skills* (Interactive keyboard-driven tag pills)
  4. *Work Experience* (Company, Role, Achievements description)
  5. *Initial Master Resume Seeding* (Auto-creates the candidate's first baseline resume)

### 2. Multi-Tenant Authentication & Security
- **Native Cryptography**: Salted **PBKDF2-HMAC-SHA256** password hashing with zero brittle external C-extension dependencies (native Python 3.13 compatible).
- **Session Tokens**: Cryptographically signed **HMAC-SHA256 JWT** access tokens with automated Bearer authorization in frontend API clients.
- **Tenant Isolation**: Strict per-user database scoping across all endpoints (`/profile`, `/resumes`, `/jobs`, `/tailoring`, `/applications`). User A cannot view, mutate, or access User B's career data.

### 3. Master Career Profile
- Serves as the candidate's immutable ground truth.
- Tracks education history, work experiences with quantified achievements, normalized technical competencies, key projects with live demo/repo links, and accredited certifications.
- **Deterministic Completeness Scoring**: Evaluates profile readiness across 7 career dimensions (0–100%).

### 4. Resume Version Control
- Supports multiple targeted resume families (e.g., *Backend Engineer - Python*, *Full Stack Engineer - React*).
- **Document Text Extraction**: Native extraction from uploaded `.pdf` and `.docx` files up to 10MB.
- **Immutable Snapshots**: Every modification produces a numbered version snapshot (`v1.0`, `v1.1`) preserving complete history.

### 5. Job Intelligence & NLP Extraction
- Instant ingestion of target job descriptions via raw text pasting or structured fields.
- NLP requirement extraction classifies postings into:
  - Mandatory required skills
  - Preferred / bonus skills
  - Experience year requirements
  - Core role responsibilities

### 6. Explainable Semantic Matching
- **Progressive Disclosure**: High-level match scores (0–100%) and plain-English summaries are shown by default so candidates immediately understand their fit.
- **Three Clear Outcome Buckets**:
  1. ✅ **Matched** — Skills and experience directly supported by candidate profile evidence.
  2. ⚡ **Partial / Highlight Needed** — Capabilities verified in the Master Profile but missing from the current resume version.
  3. ❌ **Missing** — Critical job gaps.
- Deep evidence quotes, vector similarity scores, and component mathematical weights are neatly tucked into expandable accordions (`[View evidence ▾]`).

### 7. Truth Guard 2.0 & AI Tailoring
- **Zero-Hallucination Guardrails**: Evaluates proposed bullet points clause-by-clause against the candidate's knowledge base.
- **Attribution Statuses**:
  - `VERIFIED` — 100% grounded in verified candidate facts.
  - `PARTIALLY_SUPPORTED` — Reasonable inference requiring candidate confirmation.
  - `UNSUPPORTED` — Hallucination blocked. Prohibits inventing numbers, metrics, or technologies.
- **Line-by-Line Diff & Score Delta**: Visual inspection of added (`+`) and removed (`-`) lines alongside before-and-after match score improvements.

### 8. Applications Pipeline Tracker
- Full Kanban-style pipeline tracking across 6 stages: `Applied`, `Screening`, `Interviewing`, `Offered`, `Rejected`, and `Withdrawn`.
- Direct linkage to target job descriptions and the exact tailored resume version sent to recruiters.

### 9. Responsive Design & Mobile Navigation
- **Desktop**: Collapsible navigation sidebar (icon-only `w-16` or expanded `w-64`).
- **Mobile**: Touch-optimized slide-over drawer with dark blur backdrop (`< 768px`).
- **Thumb-Friendly Bottom Navigation**: Fixed 64px mobile navigation bar with 48px+ touch targets for rapid one-handed navigation.

---

## Technology Stack

| Layer | Technologies | Details |
|---|---|---|
| **Frontend** | Next.js 14, React 18, TypeScript | App Router, Tailwind CSS, shadcn/ui, Lucide Icons, Sonner |
| **State & API** | TanStack React Query, Zustand | Optimistic updates, Bearer auth interceptors |
| **Backend** | FastAPI, Pydantic v2, Python 3.13 | Async endpoints, dependency injection, typing |
| **ORM & Database** | SQLAlchemy 2.0 (Async), Alembic | PostgreSQL 16 with `pgvector 0.8.6` |
| **Cache & Tasks** | Memurai (Redis on Windows) / Redis 7.4 | Celery 5.x async worker (`-P solo` for Windows) |
| **AI / LLMs** | Google Gemini 2.5 Flash / Ollama | Primary cloud inference + local `llama3.1:8b` fallback |
| **Embeddings** | Gemini text-embedding / `all-MiniLM-L6-v2` | 768/384-dimensional cosine vector similarity |
| **Parsing** | PyPDF, python-docx | Text extraction from `.pdf` and `.docx` |

---

## Repository Structure

```
ResumeForge/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/v1/endpoints/  # auth, profile, resumes, jobs, tailoring, applications
│   │   │   ├── core/              # security, config, dependencies, database session
│   │   │   ├── models/            # SQLAlchemy ORM models (User, Profile, Resume, Job, Match)
│   │   │   ├── schemas/           # Pydantic v2 request/response schemas
│   │   │   ├── services/          # Business logic: Auth, Truth Guard, Match, Tailor, Diff
│   │   │   └── workers/           # Celery tasks and app configuration
│   │   ├── alembic/               # Database schema migrations (001 through 005)
│   │   ├── pyproject.toml         # Python backend dependencies
│   │   └── tests/                 # 91 unit and integration tests
│   │
│   └── frontend/
│       ├── src/
│       │   ├── app/
│       │   │   ├── (auth)/        # /login, /register
│       │   │   ├── (dashboard)/   # /dashboard, /profile, /resumes, /jobs, /applications, /settings
│       │   │   ├── onboarding/    # 5-step guided candidate onboarding wizard
│       │   │   └── page.tsx       # Welcome landing page
│       │   ├── components/        # UI components, layout shell, topbar, responsive sidebar
│       │   ├── lib/               # AuthContext, API client, hooks, Zustand stores
│       │   └── types/             # TypeScript domain interfaces
│       └── package.json           # Frontend dependencies
│
├── scripts/                       # Verification scripts (consumer journey, services, health checks)
├── docs/                          # Architecture diagrams and specifications
├── .env.windows.example           # Reference Windows-native environment template
└── README.md
```

---

## Local Development (Windows 11 Native)

ResumeForge runs 100% natively on Windows 11 without requiring Docker Desktop or WSL.

### 1. Prerequisites
- **Python 3.11–3.13** installed and on `PATH`.
- **Node.js 20+ / npm** installed and on `PATH`.
- **PostgreSQL 16** running as a Windows service (`postgresql-x64-16`) with `pgvector 0.8.6` installed.
- **Memurai** (Redis-compatible service) running on `localhost:6379`.
- **Gemini API Key** *(recommended)* or **Ollama** running locally.

### 2. Configure Environment Files

**Backend Configuration (`apps/backend/.env`):**
```env
APP_NAME=ResumeForge
ENVIRONMENT=development
DEBUG=true

# Database (PostgreSQL + asyncpg)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resumeforge
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/resumeforge

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AI Inference (Gemini or Ollama)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_PROVIDER=gemini

# Security
SECRET_KEY=generate_a_secure_random_hex_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Frontend Configuration (`apps/frontend/.env.local`):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Security Rule:** Never commit `.env` or `.env.local` files to version control. Both are safely ignored by `.gitignore`.

### 3. Run Database Migrations

Apply all schema migrations up to head (`005_user_auth_schema`):

```powershell
cd D:\ResumeForge\apps\backend
python -m alembic upgrade head
```

### 4. Start the Application

Open three separate terminal windows:

**Terminal 1 — Backend (FastAPI):**
```powershell
cd D:\ResumeForge\apps\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend (Next.js):**
```powershell
cd D:\ResumeForge\apps\frontend
npm run dev
```

**Terminal 3 — Background Worker (Celery):**
```powershell
cd D:\ResumeForge\apps\backend
$env:PYTHONPATH="."
celery -A app.workers.celery_app worker -P solo -l info
```

Open your browser at **`http://localhost:3000`**.

---

## Docker Alternative (Containerized)

For Linux/macOS or deployment environments, containerized execution via Docker Compose is available:

```bash
# Build and start all services (PostgreSQL, Redis, Celery, FastAPI, Next.js)
docker compose up -d

# Check service logs
docker compose logs -f backend
```

---

## Environment Variables

| Variable | Description | Default / Example | Required? |
|---|---|---|:---:|
| `DATABASE_URL` | Async PostgreSQL connection string for asyncpg | `postgresql+asyncpg://postgres:...@localhost:5432/resumeforge` | **Yes** |
| `REDIS_URL` | Redis / Memurai connection string | `redis://localhost:6379/0` | **Yes** |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` | **Yes** |
| `LLM_PROVIDER` | Active LLM inference provider (`gemini` or `ollama`) | `gemini` | **Yes** |
| `GEMINI_API_KEY` | Google AI Studio Gemini API key | `AIzaSy...` | If using Gemini |
| `GEMINI_MODEL` | Target Gemini model | `gemini-2.5-flash` | No |
| `OLLAMA_BASE_URL` | Local Ollama endpoint | `http://localhost:11434` | If using Ollama |
| `SECRET_KEY` | HMAC secret for JWT signing | 64-char hex string | **Yes** |
| `NEXT_PUBLIC_API_URL` | Backend URL exposed to the Next.js client | `http://localhost:8000` | **Yes** |

---

## Testing & Quality Assurance

ResumeForge maintains rigorous automated verification across both unit and end-to-end integration boundaries:

### 1. Backend Automated Test Suite (91 Tests)
Covers authentication, multi-tenant isolation, profile management, resume versioning, job parsing, semantic matching, Truth Guard 2.0, tailoring diffs, and application tracking:

```powershell
cd D:\ResumeForge
$env:PYTHONPATH="apps/backend"
python -m pytest tests/backend/ -q
```
**Status: 91/91 Passed (100% Pass Rate)**

### 2. Frontend Production Build (15 Routes)
Verifies TypeScript type checking, static optimization, and App Router page bundling:

```powershell
cd D:\ResumeForge\apps\frontend
npm run build
```
**Status: 15/15 Routes Compiled with 0 Errors, 0 Warnings**

### 3. End-to-End Consumer Journey Verification
Executes an automated, live multi-step user journey against both the backend and frontend:
1. Public visitor visits `/`, `/login`, `/register`, `/onboarding`
2. User registers via `/api/v1/auth/register` and receives JWT
3. User completes 5-step onboarding wizard
4. User creates baseline resume snapshot `v1.0`
5. Ingests full-stack engineer job posting and extracts requirements
6. Evaluates semantic match (score: `69.6/100`)
7. Audits tailoring suggestions with Truth Guard 2.0 (hallucinations blocked)
8. Applies verified improvements to generate tailored version `v1.1`
9. Logs application in pipeline and advances stage to `SCREENING`
10. Validates multi-tenant scoping and verifies all 14 dynamic/static frontend routes

```powershell
python scripts/verify_consumer_journey.py
```
**Status: All 11/11 Steps Verified 100%**

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
