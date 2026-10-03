"""Tests for Celery worker configuration and task execution.

These tests do NOT require a running Redis broker.  They use Celery's
``ALWAYS_EAGER`` mode (``task.apply()``) to execute tasks in-process,
and inspect configuration directly without connecting to a broker.
"""

from __future__ import annotations


class TestCeleryAppConfiguration:
    """Verify the Celery application is correctly configured."""

    def test_celery_app_is_importable(self) -> None:
        """celery_app can be imported from the workers module."""
        from app.workers.celery_app import celery_app

        assert celery_app is not None

    def test_broker_matches_settings(self, settings) -> None:
        """Celery broker URL matches settings.CELERY_BROKER_URL."""
        from app.workers.celery_app import celery_app

        assert celery_app.conf.broker_url == settings.CELERY_BROKER_URL

    def test_backend_matches_settings(self, settings) -> None:
        """Celery result backend matches settings.CELERY_RESULT_BACKEND."""
        from app.workers.celery_app import celery_app

        assert celery_app.conf.result_backend == settings.CELERY_RESULT_BACKEND

    def test_task_serializer_is_json(self) -> None:
        """Tasks are serialised as JSON."""
        from app.workers.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"

    def test_result_serializer_is_json(self) -> None:
        """Results are serialised as JSON."""
        from app.workers.celery_app import celery_app

        assert celery_app.conf.result_serializer == "json"

    def test_task_track_started_enabled(self) -> None:
        """task_track_started is True so in-progress tasks are visible."""
        from app.workers.celery_app import celery_app

        assert celery_app.conf.task_track_started is True

    def test_timezone_is_utc(self) -> None:
        """Worker timezone is UTC."""
        from app.workers.celery_app import celery_app

        assert celery_app.conf.timezone == "UTC"


class TestHealthCheckTask:
    """Verify the foundation.health_check task is registered and executable."""

    def test_task_is_registered(self) -> None:
        """foundation.health_check appears in Celery's task registry."""
        from app.workers.celery_app import celery_app
        from app.workers.tasks import foundation  # noqa: F401 — triggers registration

        assert "foundation.health_check" in celery_app.tasks

    def test_task_execution_eager(self) -> None:
        """Task executes synchronously via apply() and returns expected shape."""
        from app.workers.tasks.foundation import health_check

        # apply() runs the task eagerly in the current process without a broker.
        result = health_check.apply()
        payload = result.get()

        assert payload["status"] == "ok"
        assert "worker" in payload
        assert "timestamp" in payload
        assert "message" in payload

    def test_task_message_content(self) -> None:
        """Task message confirms worker is operational."""
        from app.workers.tasks.foundation import health_check

        result = health_check.apply()
        payload = result.get()

        assert "ResumeForge" in payload["message"]
        assert "operational" in payload["message"]

    def test_task_timestamp_is_string(self) -> None:
        """Timestamp is returned as an ISO-8601 formatted string."""
        from app.workers.tasks.foundation import health_check

        result = health_check.apply()
        payload = result.get()

        # Basic ISO-8601 format check: contains 'T' separator
        assert isinstance(payload["timestamp"], str)
        assert "T" in payload["timestamp"]
