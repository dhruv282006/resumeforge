# ResumeForge Backend

FastAPI-powered REST API and Celery worker engine for ResumeForge.

## Local Windows Development

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Start FastAPI development server
uvicorn app.main:app --reload --port 8000

# 3. Start Celery worker (in a separate terminal)
celery -A app.workers.celery_app worker --loglevel=info -P solo
```
