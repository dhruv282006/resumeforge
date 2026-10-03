"""Alembic environment configuration for ResumeForge.

This file is executed by Alembic for both ``alembic upgrade`` (online mode)
and offline SQL script generation.  The database URL is always read from
the application settings so there is a single source of truth for the
connection string.

Supports async migrations via :func:`asyncio.run`.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Import Base so Alembic can discover all model metadata.
# Even though no models exist yet, this ensures migrations work correctly
# once models are added.
from app.core.database import Base
from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini
# ---------------------------------------------------------------------------

config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the sqlalchemy.url with the value from pydantic-settings so we
# never need to put a real connection string in alembic.ini.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Metadata used by Alembic's auto-generation (--autogenerate).
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations (generate SQL script without a live DB connection)
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In this mode Alembic does not need a real database connection — it
    generates SQL that can be reviewed and applied manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (apply directly against a live database)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Execute pending migrations using an established database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside an async context."""
    connectable: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
