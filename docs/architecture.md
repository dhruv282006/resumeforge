# ResumeForge Architecture

> This document provides the system architecture for ResumeForge — an AI-powered Resume Engineering SaaS platform.

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture Diagram](#high-level-architecture-diagram)
3. [Service Responsibilities](#service-responsibilities)
4. [Database Approach](#database-approach)
5. [Async Task Pipeline](#async-task-pipeline)
6. [AI Provider Abstraction](#ai-provider-abstraction)
7. [Data Flow: Resume Analysis](#data-flow-resume-analysis)
8. [Network Topology](#network-topology)
9. [Development vs. Production](#development-vs-production)

---

## System Overview

ResumeForge is a full-stack SaaS application built as a **monorepo** with a
clear separation between:

- **Frontend** – Next.js 14 (App Router) served on port 3000
- **Backend** – FastAPI (Python 3.11) served on port 8000
- **Infrastructure** – PostgreSQL 16 + pgvector, Redis 7, Celery workers
- **AI Layer** – Provider-agnostic LLM abstraction (Ollama / OpenAI / Gemini)

All services communicate over an internal Docker network (`resumeforge-network`).
The only publicly exposed ports are 3000, 8000, and 8025 (MailHog).

---

## High-Level Architecture Diagram

```mermaid
flowchart TD
    Browser["Browser / Client"]
    FE["Frontend\nNext.js :3000"]
    BE["Backend\nFastAPI :8000"]
    CW["Celery Worker"]
    PG["PostgreSQL :5432\n+ pgvector"]
    RD["Redis :6379"]
    MH["MailHog :1025/:8025"]
    LLM["LLM Provider\nOllama / OpenAI / Gemini"]

    Browser -->|"HTTPS / REST"| FE
    FE -->|"REST API"| BE
    BE -->|"SQLAlchemy async"| PG
    BE -->|"Enqueue tasks"| RD
    RD -->|"Task dispatch"| CW
    CW -->|"DB writes"| PG
    CW -->|"AI calls"| LLM
    BE -->|"AI calls (sync)"| LLM
    BE -->|"SMTP"| MH
    CW -->|"SMTP"| MH
```

---

## Service Responsibilities

| Service | Image | Responsibility |
|---|---|---|
| **postgres** | `pgvector/pgvector:pg16` | Primary relational store + vector similarity search |
| **redis** | `redis:7.4-alpine` | Celery broker (DB 0), result backend (DB 1), cache |
| **mailhog** | `mailhog/mailhog:latest` | Local SMTP trap; view emails at http://localhost:8025 |
| **backend** | Custom (Python 3.11) | REST API, auth, business logic, LLM orchestration |
| **celery_worker** | Same image as backend | Long-running async jobs: resume parsing, AI analysis |
| **frontend** | Custom (Node.js 20) | React UI, server-side rendering, file upload |

---

## Database Approach

### PostgreSQL 16 + pgvector

ResumeForge uses a single **PostgreSQL** instance with the **pgvector** extension
(`pgvector/pgvector:pg16`) for:

- **Relational data** — users, resumes, job descriptions, analysis results
- **Vector embeddings** — resume section embeddings and JD embeddings stored as
  `vector(1536)` columns, enabling cosine-similarity search for matching

### Schema Management

Database schema is managed with **Alembic** (SQLAlchemy migrations).

```
apps/backend/
  alembic/
    versions/      ← migration files (auto-generated + hand-edited)
    env.py
  app/
    models/        ← SQLAlchemy ORM models
```

### Connection Strings

| Context | URL Pattern |
|---|---|
| Inside Docker (async) | `postgresql+asyncpg://user:pass@postgres:5432/resumeforge` |
| Inside Docker (sync/Alembic) | `postgresql://user:pass@postgres:5432/resumeforge` |
| Local dev (outside Docker) | `postgresql+asyncpg://user:pass@localhost:5432/resumeforge` |

---

## Async Task Pipeline

Long-running operations (resume parsing, LLM inference, PDF generation) are
offloaded to **Celery workers** to keep the API responsive.

```
Client ──POST /api/v1/resumes/analyze──► FastAPI
                                            │
                                    Enqueue task to Redis
                                            │
                                    Return { task_id, status: "queued" }

Client ──GET /api/v1/tasks/{task_id}──► FastAPI ──► Redis (result backend)
                                            │
                                    Return { status, result }

                     Redis ──dispatch──► Celery Worker
                                            │
                                    ┌── LLM call (OpenAI / Ollama)
                                    ├── Parse PDF/DOCX
                                    ├── Generate embeddings
                                    └── Write results to PostgreSQL
```

### Task Categories (Phase 2+)

| Task | Module | Description |
|---|---|---|
| `parse_resume` | `app.workers.tasks.parsing` | Extract text from PDF/DOCX |
| `analyze_resume` | `app.workers.tasks.analysis` | LLM-powered gap analysis |
| `generate_embeddings` | `app.workers.tasks.embeddings` | Vector embedding generation |
| `send_email` | `app.workers.tasks.email` | Async transactional emails |

---

## AI Provider Abstraction

The `LLM_PROVIDER` environment variable controls which AI backend is used.
All providers implement the same internal interface so the business logic is
provider-agnostic.

```
LLM_PROVIDER=ollama   →  Ollama (local, free, no API key)
LLM_PROVIDER=openai   →  OpenAI GPT-4o (requires OPENAI_API_KEY)
LLM_PROVIDER=gemini   →  Google Gemini 1.5 Pro (requires GEMINI_API_KEY)
```

### Provider Comparison

| Feature | Ollama | OpenAI | Gemini |
|---|---|---|---|
| Cost | Free | Pay-per-token | Pay-per-token |
| Privacy | Local (no data leaves machine) | Cloud | Cloud |
| Setup | Install + pull model | API key only | API key only |
| Speed | Depends on hardware | Fast | Fast |
| Quality | Good (llama3.1:8b) | Best | Excellent |
| Recommended for | Local dev | Production | Production alt |

Switching providers requires only changing `LLM_PROVIDER` (and the
corresponding API key) in `.env` — no code changes.

---

## Data Flow: Resume Analysis

```
User uploads PDF
      │
      ▼
Frontend (Next.js)
  POST /api/v1/resumes  (multipart/form-data)
      │
      ▼
Backend (FastAPI)
  1. Validate file type & size
  2. Store raw file to object storage (Phase 3) / local disk (Phase 1-2)
  3. Create Resume record in PostgreSQL (status=pending)
  4. Enqueue parse_resume Celery task
  5. Return { resume_id, status: "pending" }
      │
      ▼
Celery Worker
  1. Extract text (pdfplumber / python-docx)
  2. Chunk into sections (summary, experience, education, skills)
  3. Generate embeddings for each section
  4. Store chunks + embeddings in PostgreSQL
  5. Enqueue analyze_resume task
      │
      ▼
Celery Worker (analysis)
  1. Fetch resume chunks from DB
  2. Fetch job description (if provided)
  3. Build prompt → call LLM provider
  4. Parse structured response (Pydantic)
  5. Store AnalysisResult in PostgreSQL
  6. Update Resume.status = "complete"
  7. (Optional) Send email notification
      │
      ▼
Client polls GET /api/v1/resumes/{id}
  → Returns full analysis result when status=complete
```

---

## Network Topology

All Docker services share the `resumeforge-network` bridge network.
Inter-service communication uses Docker service names as hostnames.

```
resumeforge-network (bridge)
  ├── postgres     (internal: 5432,  external: 5432)
  ├── redis        (internal: 6379,  external: 6379)
  ├── mailhog      (internal: 1025/8025, external: 1025/8025)
  ├── backend      (internal: 8000,  external: 8000)
  ├── celery_worker (internal only)
  └── frontend     (internal: 3000,  external: 3000)
```

---

---

## Phase 1: Profile & Resume Core Architecture

### 1. Ground Truth Principle: Master Career Profile
In ResumeForge, the user's **Master Career Profile** is the primary source of truth:
- **Resumes are derived representations**, not sources of truth.
- All facts (skills, education, experience, achievements, metrics, projects, certifications) are rooted in verified candidate data.
- AI layer in subsequent phases can only match or tailor based on existing profile facts; fabrication is structurally prevented.

```mermaid
erDiagram
    USER ||--|| PROFILE : owns
    PROFILE ||--o{ EDUCATION : includes
    PROFILE ||--o{ EXPERIENCE : includes
    PROFILE ||--o{ SKILL : includes
    PROFILE ||--o{ PROJECT : includes
    PROFILE ||--o{ CERTIFICATION : includes
    USER ||--o{ RESUME : maintains
    RESUME ||--o{ RESUME_VERSION : versions
    RESUME_VERSION ||--o| RESUME_VERSION : parent
```

### 2. Resume Version Control Model (Git-Style Immutability)
- **Resume Families**: A user can maintain multiple resume families (e.g., General, Backend, AI/ML).
- **Immutable Snapshots**: Saved resume versions (`v1.0`, `v1.1`, `v2.0`) are never overwritten.
- **Lineage**: Each version records `parent_version_id`, `version_number`, and `change_summary`.
- **Cloning & Branching**: Users can branch a new version from any existing version.
- **Active Version Pointer**: The `Resume.active_version_id` points to the designated primary version.

### 3. Storage Abstraction
- Abstract `StorageProvider` interface (`upload`, `download`, `delete`, `exists`).
- `LocalStorageProvider` writes to `storage/resumes/{user_id}/{prefix}_{filename}`.
- Sanitizes filenames against path traversal attacks.
- Validates file size (10MB maximum limit).
- Extensible to AWS S3 / Google Cloud Storage without modifying service logic.

### 4. Document Text Extraction Pipeline
- Abstract `DocumentExtractor` interface with `extract(file_bytes) -> str`.
- `PdfExtractor` leverages `pypdf.PdfReader` to extract clean page text.
- `DocxExtractor` leverages `python-docx` to extract structured paragraphs and tables.
- Factory `get_extractor(filename_or_mime)` dynamically routes to the appropriate parser.

### 5. Profile Completeness Algorithm
Internal deterministic score (0-100%):
- **Personal Info (20%)**: Headline, summary, email, phone, location (4% each).
- **Education (15%)**: At least 1 verified education entry.
- **Experience (25%)**: At least 1 verified work experience entry.
- **Skills (20%)**: 1 skill = 10%, $\ge 3$ skills = 20%.
- **Projects (10%)**: At least 1 project entry.
- **Certifications (5%)**: At least 1 professional certification.
- **Links (5%)**: At least 1 profile link (LinkedIn, GitHub, or Portfolio).

---

## Development vs. Production

| Concern | Development | Production |
|---|---|---|
| LLM provider | Ollama (local) | OpenAI / Gemini |
| Email | MailHog (local) | SendGrid / SES |
| File storage | Local filesystem | S3 / GCS |
| Secrets | `.env` file | Vault / KMS / env injection |
| TLS | None (localhost) | nginx + Let's Encrypt |
| Scaling | Single worker | Kubernetes / ECS |
| Observability | stdout logs | Datadog / Grafana |

---

*See [development.md](development.md) for local setup instructions.*
