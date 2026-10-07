# ResumeForge — Windows Native Development Setup (Docker-Free)

This guide documents how to run **ResumeForge** natively on Windows 11 without requiring Docker Desktop, Hyper-V, or WSL.

---

## 1. System Architecture (Localhost)

```
Browser
   ↓
Next.js Frontend (Port 3000)
   ↓ HTTP / JSON API
FastAPI Backend (Port 8000)
   ├── PostgreSQL + pgvector (Port 5432)
   ├── Redis / Memurai Broker (Port 6379)
   │      └── Celery Worker (Windows -P solo)
   └── Ollama AI Engine (Port 11434, local LLM/embeddings)
```

Docker and WSL are **not** required. All components run directly as native Windows processes or Windows services.

---

## 2. Prerequisites & Installed Tools

Verify your existing tool installations in PowerShell:

| Component | Minimum Version | Verification Command |
|---|---|---|
| **Windows** | Windows 10/11 64-bit | `[System.Environment]::OSVersion` |
| **Python** | 3.11+ (3.13 supported) | `python --version` |
| **Node.js** | 18+ (22.x LTS supported) | `node --version` |
| **npm** | 10+ | `npm --version` |
| **Ollama** | Latest Windows installer | `ollama --version` |

---

## 3. External Services Installation (Windows Native)

ResumeForge requires two external database/broker services: **PostgreSQL with pgvector** and a **Redis-compatible broker (Memurai)**.

### A. PostgreSQL 16/17 Installation

You can install PostgreSQL natively using either the official GUI installer or winget.

#### Option 1: Official EDB Installer (Recommended)
1. Download the Windows installer from [EnterpriseDB PostgreSQL Downloads](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
2. Choose version **16** or **17** (64-bit).
3. During setup:
   - Installation Directory: `C:\Program Files\PostgreSQL\16`
   - Data Directory: `C:\Program Files\PostgreSQL\16\data`
   - Password: Set to `postgres` (or `resumeforge_dev_password` matching your `.env`).
   - Port: `5432`
   - Locale: Default
4. Finish installation and ensure the Windows service `postgresql-x64-16` is set to **Automatic** and **Running**.

#### Option 2: Windows Package Manager (winget)
```powershell
winget install PostgreSQL.PostgreSQL.16 --source winget
```

#### Create the Database:
Open PowerShell and create the application database:
```powershell
# Using psql:
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE resumeforge;"
```

---

### B. pgvector Extension Installation on Windows

`pgvector` provides vector similarity search for semantic resume-job matching.

#### Step 1: Precompiled pgvector Binaries
1. Visit the [pgvector GitHub Releases](https://github.com/pgvector/pgvector/releases).
2. Download the precompiled Windows zip corresponding to your PostgreSQL version (e.g., `pgvector_v0.8.0_pg16_windows_x64.zip`).
3. Extract the archive. It contains:
   - `lib\vector.dll`
   - `share\extension\vector.control`
   - `share\extension\vector--*.sql`
4. Copy these files to your PostgreSQL installation directory (requires Administrator privileges):
   - Copy `vector.dll` → `C:\Program Files\PostgreSQL\16\lib\`
   - Copy `vector.control` and all `vector--*.sql` files → `C:\Program Files\PostgreSQL\16\share\extension\`

#### Step 2: Enable the Extension
Enable the vector extension in the `resumeforge` database:
```powershell
psql -U postgres -h localhost -p 5432 -d resumeforge -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Step 3: Verify pgvector
```powershell
psql -U postgres -h localhost -p 5432 -d resumeforge -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```
Expected output:
```
 extname | extversion
---------+------------
 vector  | 0.8.0
(1 row)
```

---

### C. Redis / Memurai Installation (Windows Native)

On Linux/Docker, Redis is typically used. On Windows, the official native Redis-compatible engine is **Memurai**.

#### Option 1: Memurai Developer Edition (Recommended)
Memurai is 100% compatible with the Redis 7+ protocol and runs as a native Windows service.
1. Download the free Developer edition installer from [Memurai Downloads](https://www.memurai.com/get-memurai).
2. Run the MSI installer with default options:
   - Port: `6379`
   - Service: Runs automatically as a background service.
3. Test connectivity in PowerShell:
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet
   # Returns: True
   ```

#### Option 2: Native Redis Windows Port (Alternative)
Alternatively, download the standalone Windows Redis MSI or zip from [tporadowski/redis releases](https://github.com/tporadowski/redis/releases) and run `redis-server.exe`.

---

### D. Ollama for Windows (Local AI / Embeddings)

Ollama runs locally as a Windows application on port `11434`.

1. If not already installed, download from [Ollama for Windows](https://ollama.com/download/windows).
2. Start Ollama from the Windows Start menu or run:
   ```powershell
   & "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
   ```
3. Pull the recommended open-weights models:
   ```powershell
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```

> **Note**: If Ollama is not running, ResumeForge automatically falls back to deterministic rule-based keyword & skill matching, allowing all core resume tailoring and version control features to work seamlessly.

---

## 4. Environment Configuration

1. Copy the Windows-native template to `.env`:
   ```powershell
   Copy-Item .env.windows.example .env
   ```
2. Verify the database credentials in `.env` match your local PostgreSQL installation:
   ```ini
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resumeforge
   DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/resumeforge
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/1
   OLLAMA_BASE_URL=http://localhost:11434
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

---

## 5. Automated Setup Script

Run the automated setup script to configure the Python virtual environment and install all dependencies:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1
```

This script will:
- Verify Python and Node runtimes
- Create `apps/backend/.venv`
- Install backend dependencies in editable mode
- Check availability of PostgreSQL, pgvector, Redis, and Ollama
- Run database migrations (`alembic upgrade head`) once PostgreSQL is online

---

## 6. Audit System Health

At any time, you can run the non-destructive service checker:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-windows-services.ps1
```

---

## 7. Running ResumeForge (3 Terminals)

Once PostgreSQL and Redis are running, start the 3 components:

### Option A: Automatic Launcher
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-windows.ps1
```
This spawns 3 separate PowerShell windows for the Backend, Celery Worker, and Frontend.

### Option B: Manual Startup

#### Terminal 1 — FastAPI Backend
```powershell
cd D:\ResumeForge\apps\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

#### Terminal 2 — Celery Worker (Windows Solo Pool)
```powershell
cd D:\ResumeForge\apps\backend
.\.venv\Scripts\Activate.ps1
celery -A app.workers.celery_app worker --loglevel=info -P solo
```
> **IMPORTANT FOR WINDOWS**: Always pass `-P solo` (or `--pool=solo`). Windows does not support Unix `fork()`, so Celery's default prefork pool will raise an error. The `solo` pool executes tasks synchronously inside the worker process, which is ideal for local development.

#### Terminal 3 — Next.js Frontend
```powershell
cd D:\ResumeForge\apps\frontend
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 8. Applying Database Migrations Manually

When you modify SQLAlchemy models or pull new code, apply migrations using:

```powershell
cd D:\ResumeForge\apps\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

---

## 9. Running Tests

Run the full pytest suite (88 tests) locally using the virtual environment:

```powershell
$env:PYTHONPATH="apps/backend"
apps\backend\.venv\Scripts\python.exe -m pytest tests/backend -v --no-cov
```

Build the frontend to verify TypeScript types and page compilation:

```powershell
npm --prefix apps/frontend run build
```

---

## 10. Common Windows Pitfalls & Troubleshooting

### 1. Celery Worker fails with `ValueError: not enough values to unpack` or permission errors
- **Cause**: Celery defaults to the `prefork` process pool, which requires POSIX `fork()`.
- **Solution**: Always use `-P solo`:
  ```powershell
  celery -A app.workers.celery_app worker --loglevel=info -P solo
  ```

### 2. PowerShell execution policy blocks `.venv\Scripts\Activate.ps1`
- **Cause**: Default Windows PowerShell script execution policy is `Restricted`.
- **Solution**: Run this once in PowerShell:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

### 3. asyncpg fails with `password authentication failed for user "postgres"`
- **Cause**: Password in `.env` does not match the password set during PostgreSQL installation.
- **Solution**: Update `DATABASE_URL` in `.env` to match your actual local password.

### 4. `extension "vector" is not available` error during migration
- **Cause**: `pgvector` binaries were not copied to the PostgreSQL directory or the extension was not installed.
- **Solution**: Follow [Section 3.B](#b-pgvector-extension-installation-on-windows) to copy `vector.dll` into `C:\Program Files\PostgreSQL\<version>\lib`.
