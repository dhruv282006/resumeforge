"""Abstract LLM provider interface for ResumeForge.

All AI/LLM operations in the application must go through this interface.
Never import a specific provider directly in business logic; use the
:func:`get_llm_provider` factory instead so the active provider can be
switched via the ``LLM_PROVIDER`` environment variable without code changes.

Example::

    from app.ai.providers.base import get_llm_provider
    from app.core.config import get_settings

    provider = get_llm_provider(get_settings())
    answer = await provider.complete("Summarise this resume.")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.core.config import Settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface for all LLM providers in ResumeForge.

    All AI/LLM operations in the application must go through this interface.
    Never import a specific provider directly in business logic.

    Implementations:

    * :class:`~app.ai.providers.ollama.OllamaProvider` — local inference via Ollama.
    * :class:`~app.ai.providers.openai.OpenAIProvider` — OpenAI API (Phase 2+).
    * :class:`~app.ai.providers.gemini.GeminiProvider` — Google Gemini API (Phase 2+).
    """

    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a text completion.

        Args:
            prompt: The user-facing prompt to send to the model.
            system_prompt: Optional system/instruction prompt prepended to
                the conversation context.

        Returns:
            The model's generated text response as a plain string.
        """
        ...

    @abstractmethod
    async def extract_structured(
        self,
        prompt: str,
        schema: type[T],
        system_prompt: str = "",
    ) -> T:
        """Extract structured data conforming to a Pydantic schema.

        The provider is responsible for instructing the model to respond in
        valid JSON that matches *schema*, and for validating the response.

        Args:
            prompt: The extraction prompt describing what to extract.
            schema: A :class:`pydantic.BaseModel` subclass that defines the
                expected output structure.
            system_prompt: Optional system/instruction prompt.

        Returns:
            A validated instance of *schema*.
        """
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts.

        Args:
            texts: A list of input strings to embed.

        Returns:
            A list of embedding vectors, one per input string, in the same
            order as *texts*.
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check if the provider is reachable and operational.

        Returns:
            A dictionary with at least a ``"status"`` key.  Additional keys
            are provider-specific (e.g. available models, latency).
        """
        ...


def get_llm_provider(settings: "Settings") -> LLMProvider:
    """Return the configured LLM provider based on ``settings.LLM_PROVIDER``.

    This is the sole entry-point for obtaining an LLM provider instance.
    Business logic must **never** instantiate a provider directly.

    Args:
        settings: The application :class:`~app.core.config.Settings` instance.

    Returns:
        An :class:`LLMProvider` implementation matching ``settings.LLM_PROVIDER``.

    Raises:
        ValueError: If ``settings.LLM_PROVIDER`` names an unknown provider
            (this should not happen if the settings validator is working).
    """
    # Deferred imports avoid circular dependencies and keep unused provider
    # modules from being imported when they are not configured.
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "ollama":
        from app.ai.providers.ollama import OllamaProvider

        return OllamaProvider(settings=settings)

    if provider_name == "openai":
        from app.ai.providers.openai import OpenAIProvider

        return OpenAIProvider(settings=settings)

    if provider_name == "gemini":
        from app.ai.providers.gemini import GeminiProvider

        return GeminiProvider(settings=settings)

    raise ValueError(
        f"Unknown LLM provider {provider_name!r}. "
        "Supported values: 'ollama', 'openai', 'gemini'."
    )
