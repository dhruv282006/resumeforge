"""Foundation Celery tasks for ResumeForge.

This module contains the baseline tasks used to verify that the Celery
worker infrastructure is operational.  It is intentionally lightweight —
no database or external service calls are made here.
"""

from __future__ import annotations

import datetime

from celery import Task

from app.workers.celery_app import celery_app


@celery_app.task(name="foundation.health_check", bind=True)
def health_check(self: Task) -> dict[str, str]:
    """Verify that a Celery worker is running and can execute tasks.

    This task performs no I/O and exists solely as a liveness probe for
    the Celery worker fleet.  It can be dispatched from the API health
    endpoint or monitoring scripts.

    Args:
        self: The bound :class:`celery.Task` instance (provided by Celery
              when ``bind=True``).

    Returns:
        A dictionary containing:

        * ``status`` — always ``"ok"``.
        * ``worker`` — the hostname of the worker that executed the task.
        * ``timestamp`` — UTC ISO-8601 execution time.
        * ``message`` — human-readable confirmation string.
    """
    return {
        "status": "ok",
        "worker": self.request.hostname or "unknown",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "message": "ResumeForge Celery worker is operational",
    }
