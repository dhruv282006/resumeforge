"""Celery application factory for ResumeForge.

The Celery instance is exported as ``celery_app`` so it can be referenced
by both the worker command and task modules without circular imports.

Worker startup command::

    celery -A app.workers.celery_app:celery_app worker --loglevel=info

Beat scheduler (future use)::

    celery -A app.workers.celery_app:celery_app beat --loglevel=info
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings


def _create_celery_app() -> Celery:
    """Build and configure the Celery application from pydantic-settings.

    Returns:
        A configured :class:`celery.Celery` instance ready for worker startup.
    """
    settings = get_settings()

    app = Celery(
        "resumeforge",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "app.workers.tasks.foundation",
            "app.workers.tasks.job_tasks",
            "app.workers.tasks.tailoring_tasks",
        ],
    )

    app.conf.update(
        # Serialisation
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        # Tracking
        task_track_started=True,
        # Time zone
        timezone="UTC",
        enable_utc=True,
        # Worker behaviour
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        # Result expiry (24 hours)
        result_expires=86_400,
    )

    return app


celery_app: Celery = _create_celery_app()
