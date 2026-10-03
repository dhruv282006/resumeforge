"""Custom exception hierarchy and FastAPI exception handlers for ResumeForge.

All application-level errors descend from ``ResumeForgeError`` so callers
can distinguish library errors from framework errors with a single
``except`` clause.

The ``register_exception_handlers()`` function must be called inside the
FastAPI app factory to wire these handlers into the application.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class ResumeForgeError(Exception):
    """Base exception for all ResumeForge application errors.

    Args:
        message: Human-readable description of what went wrong.
        detail: Optional structured detail (will appear in the API response).
    """

    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFoundError(ResumeForgeError):
    """Raised when a requested resource does not exist (HTTP 404)."""

    http_status = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class ValidationError(ResumeForgeError):
    """Raised when input data fails business-rule validation (HTTP 422).

    Distinct from Pydantic's ``ValidationError`` which is caught separately.
    """

    http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"


class AuthenticationError(ResumeForgeError):
    """Raised when a request cannot be authenticated (HTTP 401)."""

    http_status = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHENTICATED"


class AuthorizationError(ResumeForgeError):
    """Raised when an authenticated user lacks required permissions (HTTP 403)."""

    http_status = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"


class ConflictError(ResumeForgeError):
    """Raised when a state conflict prevents the operation (HTTP 409)."""

    http_status = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"


class ExternalServiceError(ResumeForgeError):
    """Raised when a downstream service (DB, Redis, LLM) is unavailable (HTTP 503)."""

    http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "EXTERNAL_SERVICE_ERROR"


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------


def _error_response(
    error_code: str,
    message: str,
    detail: Any,
    http_status: int,
) -> JSONResponse:
    """Build the canonical JSON error envelope used across all error responses.

    Schema::

        {
            "error": "<ERROR_CODE>",
            "message": "<human-readable text>",
            "detail": <any | null>
        }
    """
    return JSONResponse(
        status_code=http_status,
        content={
            "error": error_code,
            "message": message,
            "detail": detail,
        },
    )


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to the FastAPI application.

    Call this function inside the app factory **before** the application
    starts handling requests.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(ResumeForgeError)
    async def resumeforge_error_handler(
        request: Request,
        exc: ResumeForgeError,
    ) -> JSONResponse:
        """Handle any ``ResumeForgeError`` and its subclasses."""
        return _error_response(
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail,
            http_status=exc.http_status,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic / FastAPI request validation failures (HTTP 422)."""
        return _error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed.",
            detail=exc.errors(),
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all handler for unexpected exceptions.

        Prevents raw tracebacks from leaking to API consumers.
        """
        return _error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            detail=None,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
