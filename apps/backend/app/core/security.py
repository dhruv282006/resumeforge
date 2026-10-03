"""JWT utility stubs for Phase 1.

Full JWT implementation (token creation, refresh, blacklisting) will be
added in a later phase.  These stubs establish the module interface so
that dependent modules can import from here without changes when the real
implementation arrives.
"""

from __future__ import annotations

from app.core.config import get_settings


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The token subject (typically a user ID).

    Returns:
        A signed JWT string.

    Raises:
        NotImplementedError: This method is not yet implemented in Phase 1.
    """
    raise NotImplementedError(
        "JWT access token creation is not yet implemented. "
        "This will be completed in Phase 2 (authentication)."
    )


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token.

    Args:
        subject: The token subject (typically a user ID).

    Returns:
        A signed JWT string.

    Raises:
        NotImplementedError: This method is not yet implemented in Phase 1.
    """
    raise NotImplementedError(
        "JWT refresh token creation is not yet implemented. "
        "This will be completed in Phase 2 (authentication)."
    )


def decode_token(token: str) -> dict[str, object]:
    """Decode and validate a JWT token.

    Args:
        token: The raw JWT string to decode.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        NotImplementedError: This method is not yet implemented in Phase 1.
    """
    raise NotImplementedError(
        "JWT token decoding is not yet implemented. "
        "This will be completed in Phase 2 (authentication)."
    )
