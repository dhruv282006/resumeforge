"""Application configuration via pydantic-settings.

All runtime configuration is sourced exclusively from environment variables
(or a .env file in the backend root). No secrets are hard-coded here.
"""

from __future__ import annotations

import functools
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object for the ResumeForge backend.

    Values are loaded in priority order:
      1. Real environment variables
      2. Variables declared in a .env file (if present)
      3. Field defaults defined below

    Required fields (no default) will raise a ``ValidationError`` at startup
    if they are not provided, which is intentional — fail-fast is safer than
    running with missing configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    APP_NAME: str = "ResumeForge"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ------------------------------------------------------------------ #
    # API
    # ------------------------------------------------------------------ #
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # ------------------------------------------------------------------ #
    # Database  (required — no default)
    # ------------------------------------------------------------------ #
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ------------------------------------------------------------------ #
    # Redis  (required — no default)
    # ------------------------------------------------------------------ #
    REDIS_URL: str

    # ------------------------------------------------------------------ #
    # Celery  (required — no default)
    # ------------------------------------------------------------------ #
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # ------------------------------------------------------------------ #
    # AI / LLM providers
    # ------------------------------------------------------------------ #
    LLM_PROVIDER: str = "ollama"  # ollama | openai | gemini

    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GEMINI_EMBED_MODEL: str = "text-embedding-004"

    # ------------------------------------------------------------------ #
    # Security (stubs — Phase 1)
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure ENVIRONMENT is one of the recognised deployment tiers."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got {v!r}")
        return v

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Ensure LLM_PROVIDER names a supported provider."""
        allowed = {"ollama", "openai", "gemini"}
        if v not in allowed:
            raise ValueError(f"LLM_PROVIDER must be one of {allowed}, got {v!r}")
        return v


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton.

    Uses ``lru_cache`` so the .env file is read only once per process
    lifetime.  During tests, call ``get_settings.cache_clear()`` before
    overriding environment variables.
    """
    return Settings()
