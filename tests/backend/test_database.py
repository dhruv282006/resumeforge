"""Tests for app/core/database.py.

These tests verify the database module structure and configuration without
requiring a real PostgreSQL connection. Live connectivity is not tested here
— that is covered by integration tests that require a running database.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDatabaseConfiguration:
    """Verify the database module reads configuration correctly."""

    def test_database_url_read_from_settings(self, settings) -> None:
        """DATABASE_URL in settings is the expected test value."""
        assert settings.DATABASE_URL == "postgresql+asyncpg://test:test@localhost:5432/test_db"

    def test_database_pool_size_has_default(self, settings) -> None:
        """DATABASE_POOL_SIZE has a sensible default."""
        assert settings.DATABASE_POOL_SIZE == 10

    def test_database_max_overflow_has_default(self, settings) -> None:
        """DATABASE_MAX_OVERFLOW has a sensible default."""
        assert settings.DATABASE_MAX_OVERFLOW == 20


class TestDatabaseEngine:
    """Verify the SQLAlchemy engine is created with the correct parameters."""

    def test_engine_is_created(self) -> None:
        """The module-level ``engine`` object is not None."""
        from app.core.database import engine

        assert engine is not None

    def test_engine_url_matches_settings(self, settings) -> None:
        """The engine URL matches the DATABASE_URL from settings."""
        from app.core.database import engine

        engine_url = engine.url.render_as_string(hide_password=False)
        assert engine_url == settings.DATABASE_URL

    def test_async_session_local_is_configured(self) -> None:
        """AsyncSessionLocal session factory is importable and not None."""
        from app.core.database import AsyncSessionLocal

        assert AsyncSessionLocal is not None


class TestGetDbDependency:
    """Verify the get_db() FastAPI dependency behaves as an async generator."""

    def test_get_db_is_async_generator_function(self) -> None:
        """get_db must be an async generator function for FastAPI DI."""
        from app.core.database import get_db

        assert inspect.isasyncgenfunction(get_db)

    def test_get_db_returns_async_generator(self) -> None:
        """Calling get_db() without awaiting returns an async generator."""
        from app.core.database import get_db

        gen = get_db()
        assert isinstance(gen, AsyncGenerator)


class TestCheckDatabaseConnection:
    """Verify the check_database_connection() health probe."""

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self) -> None:
        """Returns True when SELECT 1 executes without error."""
        from app.core.database import check_database_connection

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=None)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)

        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_conn

        with patch("app.core.database.engine", mock_engine):
            result = await check_database_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_exception(self) -> None:
        """Returns False when the engine raises an exception."""
        from sqlalchemy.exc import OperationalError

        from app.core.database import check_database_connection

        mock_engine = MagicMock()
        mock_engine.connect.side_effect = OperationalError("conn", {}, Exception("refused"))

        with patch("app.core.database.engine", mock_engine):
            result = await check_database_connection()

        assert result is False


class TestBase:
    """Verify the ORM DeclarativeBase is properly exported."""

    def test_base_is_importable(self) -> None:
        """Base can be imported from app.core.database."""
        from app.core.database import Base

        assert Base is not None

    def test_base_has_metadata(self) -> None:
        """Base exposes a metadata object for Alembic autogenerate."""
        from app.core.database import Base

        assert hasattr(Base, "metadata")
        assert Base.metadata is not None
