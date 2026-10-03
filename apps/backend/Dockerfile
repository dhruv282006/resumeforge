FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency declaration first (layer-cache friendly)
COPY pyproject.toml .

# Install Python dependencies
# Falls back gracefully if pyproject.toml extras aren't all resolvable yet
RUN uv pip install --system \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    asyncpg \
    alembic \
    redis \
    "celery[redis]" \
    httpx \
    structlog \
    python-dotenv \
    psycopg2-binary \
    pytest \
    pytest-asyncio \
    httpx

# Copy the rest of the application source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
