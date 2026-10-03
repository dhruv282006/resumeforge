"""Health check endpoint — GET /api/v1/health.

Reports the real operational status of the application and its critical
downstream dependencies (PostgreSQL and Redis).  This endpoint is designed
to be safe to call at any time: it will never raise an unhandled exception
regardless of service availability.
"""

from __future__ import annotations

import datetime
import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import check_database_connection
from app.core.redis import check_redis_connection

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ServiceStatus(BaseModel):
    """Health status for a single downstream service."""

    status: str  # "ok" | "error"
    latency_ms: float


class HealthResponse(BaseModel):
    """Top-level health check response payload."""

    status: str  # "healthy" | "degraded" | "unhealthy"
    version: str
    environment: str
    timestamp: str
    services: dict[str, ServiceStatus]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
    description=(
        "Returns the operational status of the ResumeForge API and its "
        "critical dependencies (database and Redis).  Always returns HTTP 200 "
        "so that load-balancers can distinguish between a *degraded* service "
        "and a completely unreachable one."
    ),
)
async def health_check() -> HealthResponse:
    """Perform real connectivity checks against all critical services.

    Returns:
        A :class:`HealthResponse` with aggregate status and per-service
        latency information.

    Status meanings:

    * ``"healthy"`` — all services responded successfully.
    * ``"degraded"`` — one or more services failed; the API is partially
      operational.
    * ``"unhealthy"`` — all services failed (currently unused; reserved for
      future liveness-probe semantics).
    """
    settings = get_settings()

    # ---- Database --------------------------------------------------------
    db_start = time.monotonic()
    db_ok = await _safe_check(check_database_connection)
    db_latency = (time.monotonic() - db_start) * 1000

    # ---- Redis -----------------------------------------------------------
    redis_start = time.monotonic()
    redis_ok = await _safe_check(check_redis_connection)
    redis_latency = (time.monotonic() - redis_start) * 1000

    # ---- Aggregate -------------------------------------------------------
    all_ok = db_ok and redis_ok
    aggregate_status = "healthy" if all_ok else "degraded"

    return HealthResponse(
        status=aggregate_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        services={
            "database": ServiceStatus(
                status="ok" if db_ok else "error",
                latency_ms=round(db_latency, 3),
            ),
            "redis": ServiceStatus(
                status="ok" if redis_ok else "error",
                latency_ms=round(redis_latency, 3),
            ),
        },
    )


async def _safe_check(check_fn: object) -> bool:
    """Call an async health-check function, returning ``False`` on any exception.

    Args:
        check_fn: An async callable that returns ``bool``.

    Returns:
        The boolean result of the check, or ``False`` if the check raised.
    """
    try:
        return await check_fn()  # type: ignore[operator]
    except Exception:
        return False
