"""Structured logging configuration for ResumeForge.

In *development* the log output is human-readable (coloured console).
In *staging* and *production* all events are emitted as JSON so they can
be ingested by log aggregation systems (e.g. Datadog, Loki, CloudWatch).

Call ``configure_logging()`` once during application startup (inside the
FastAPI lifespan handler) before any log statements are made.
"""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import EventDict, WrappedLogger


def _add_log_level(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Structlog processor that adds the log level name to the event dict."""
    event_dict["level"] = method_name.upper()
    return event_dict


def configure_logging(environment: str = "development") -> None:
    """Initialise structlog with environment-appropriate renderers.

    Args:
        environment: The deployment environment string (``"development"``,
            ``"staging"``, or ``"production"``).  Any value other than
            ``"development"`` triggers JSON output.
    """
    is_development = environment == "development"

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        _add_log_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_development:
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.DEBUG if is_development else logging.INFO)

    # Silence noisy third-party loggers.
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(
            logging.WARNING if not is_development else logging.INFO
        )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog-bound logger.

    Args:
        name: Optional logger name (defaults to the calling module's name
            when ``None``).

    Returns:
        A ``structlog.stdlib.BoundLogger`` ready for structured logging.

    Example::

        logger = get_logger(__name__)
        logger.info("service_started", port=8000)
    """
    return structlog.get_logger(name)
