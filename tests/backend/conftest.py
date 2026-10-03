"""Pytest configuration and shared fixtures for ResumeForge backend tests."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set required env vars BEFORE importing app modules so pydantic-settings
# picks them up. These are test-only values.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/2")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/3")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "true")

import app.models  # noqa: F401 - Register all models on Base.metadata
from app.core.database import Base, get_db
from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def settings():
    from app.core.config import get_settings

    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def mock_db_healthy():
    with patch(
        "app.api.v1.endpoints.health.check_database_connection",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_db_unhealthy():
    with patch(
        "app.api.v1.endpoints.health.check_database_connection",
        new_callable=AsyncMock,
        return_value=False,
    ) as mock:
        yield mock


@pytest.fixture
def mock_redis_healthy():
    with patch(
        "app.api.v1.endpoints.health.check_redis_connection",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_redis_unhealthy():
    with patch(
        "app.api.v1.endpoints.health.check_redis_connection",
        new_callable=AsyncMock,
        return_value=False,
    ) as mock:
        yield mock


@pytest_asyncio.fixture
async def async_client(
    mock_db_healthy: AsyncMock,
    mock_redis_healthy: AsyncMock,
) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def async_client_no_mocks() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated in-memory SQLite database session for unit/service tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client_with_db(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client backed by in-memory SQLite for testing API endpoints."""
    async def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as client:
        yield client
    fastapi_app.dependency_overrides.pop(get_db, None)
