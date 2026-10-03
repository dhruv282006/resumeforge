"""OpenAI LLM provider placeholder for ResumeForge.

This module satisfies the :class:`~app.ai.providers.base.LLMProvider`
interface but raises :class:`NotImplementedError` for all generative
operations.  Full implementation is planned for Phase 2.

To use OpenAI in development: set ``LLM_PROVIDER=openai`` in your ``.env``
and be aware that all calls will fail until this provider is implemented.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.providers.base import LLMProvider
from app.core.config import Settings
from app.core.logging import get_logger

T = TypeVar("T", bound=BaseModel)

logger = get_logger(__name__)

_NOT_IMPLEMENTED_MSG = (
    "OpenAI provider is not yet implemented. "
    "Set LLM_PROVIDER=ollama for development."
)


class OpenAIProvider(LLMProvider):
    """Placeholder OpenAI provider — all methods raise NotImplementedError.

    Args:
        settings: Application settings.  The constructor logs a warning if
            ``OPENAI_API_KEY`` is empty, as this will cause failures once
            the real implementation is added.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.OPENAI_API_KEY:
            logger.warning(
                "openai_api_key_missing",
                message=(
                    "OPENAI_API_KEY is not set. OpenAI provider will not "
                    "function even after Phase 2 implementation."
                ),
            )
        self._model = settings.OPENAI_MODEL
        self._embed_model = settings.OPENAI_EMBED_MODEL

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def extract_structured(
        self,
        prompt: str,
        schema: type[T],
        system_prompt: str = "",
    ) -> T:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def embed(self, text: str) -> list[float]:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Not yet implemented.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(_NOT_IMPLEMENTED_MSG)

    async def health_check(self) -> dict[str, Any]:
        """Return a structured response indicating this provider is not implemented.

        Returns:
            A dictionary with ``"status": "not_implemented"`` and
            ``"provider": "openai"``.
        """
        return {
            "status": "not_implemented",
            "provider": "openai",
            "message": _NOT_IMPLEMENTED_MSG,
        }
