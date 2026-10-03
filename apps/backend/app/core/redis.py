"""Redis client factory and connection health-check helper.

The client is created lazily (never at module import time) so that
application tests can patch ``get_settings()`` before a real connection
attempt is made.
"""

from __future__ import annotations

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import get_settings

# Module-level placeholder; the real client is built on first call to
# get_redis() to support lazy initialisation.
_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client, creating it on first call.

    The client is intentionally *not* created at import time so that
    integration tests can control the connection URL via environment
    variables before the first call.

    Returns:
        An ``aioredis.Redis`` instance connected to ``settings.REDIS_URL``.
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def check_redis_connection() -> bool:
    """Send a ``PING`` command to verify Redis is reachable.

    Returns:
        ``True`` if Redis responds with ``PONG``, ``False`` otherwise.
    """
    try:
        client = get_redis()
        result = await client.ping()
        return bool(result)
    except (RedisError, OSError, Exception):
        return False
