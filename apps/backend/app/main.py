"""FastAPI application factory for ResumeForge.

Usage::

    uvicorn app.main:app --reload

The ``app`` object at module level is created by calling ``create_app()``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import api_v1_router


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    This factory:

    1. Configures structured logging (JSON in production, console in dev).
    2. Creates the FastAPI instance with appropriate documentation settings.
    3. Registers CORS middleware from ``settings.ALLOWED_ORIGINS``.
    4. Attaches custom exception handlers.
    5. Mounts the ``/api/v1`` router.
    6. Registers a lifespan handler for startup/shutdown events.

    Returns:
        A fully-configured :class:`FastAPI` application ready for serving.
    """
    settings = get_settings()

    # Configure logging as early as possible so all subsequent code can log.
    configure_logging(environment=settings.ENVIRONMENT)
    logger = get_logger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Handle application startup and shutdown lifecycle events."""
        logger.info(
            "resumeforge_startup",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            debug=settings.DEBUG,
        )
        yield
        logger.info("resumeforge_shutdown", app_name=settings.APP_NAME)

    # Disable interactive docs in production to reduce attack surface.
    docs_url = "/docs" if settings.DEBUG else None
    redoc_url = "/redoc" if settings.DEBUG else None
    openapi_url = "/openapi.json" if settings.DEBUG else None

    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "ResumeForge — AI-powered Resume Engineering SaaS. "
            "Backend REST API."
        ),
        version=settings.APP_VERSION,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # ---- CORS ------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Exception handlers ----------------------------------------------
    register_exception_handlers(application)

    # ---- Routers ---------------------------------------------------------
    application.include_router(
        api_v1_router,
        prefix=settings.API_V1_PREFIX,
    )

    return application


# Module-level app instance consumed by uvicorn / gunicorn.
app: FastAPI = create_app()
