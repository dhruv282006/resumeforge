"""Async SQLAlchemy engine, session factory, and connection helpers.

All database I/O in ResumeForge is async-first.  Synchronous access (e.g.
for Alembic migrations) must go through a separate sync engine created
inside ``alembic/env.py``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models in ResumeForge.

    Import and subclass this ``Base`` in every model module so that
    Alembic's auto-generation can discover all table definitions via
    ``Base.metadata``.
    """


def _build_engine() -> AsyncEngine:
    """Construct the async SQLAlchemy engine from application settings.

    The engine is created lazily (on first import that triggers module
    initialisation) to allow test code to override settings before the
    engine is built.
    """
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
        future=True,
    )


# Module-level engine and session factory.
# Using a factory function for the engine means tests can patch get_settings()
# before these are evaluated; in production the module is imported once.
engine: AsyncEngine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request.

    The session is automatically closed (and the connection returned to
    the pool) when the request context exits, regardless of whether the
    handler raised an exception.

    Usage::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Execute a lightweight ``SELECT 1`` to verify the DB is reachable.

    Returns:
        ``True`` if the query succeeds, ``False`` on any database error.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except (OperationalError, Exception):
        return False
