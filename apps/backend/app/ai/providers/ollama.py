"""Ollama LLM provider implementation for ResumeForge.

Uses the Ollama HTTP API (https://github.com/ollama/ollama/blob/main/docs/api.md)
via :mod:`httpx` async client.  All network errors are translated into
:class:`~app.core.exceptions.ExternalServiceError` so callers can handle
them uniformly without knowing the underlying transport.
"""

from __future__ import annotations

import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.ai.providers.base import LLMProvider
from app.core.config import Settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger

T = TypeVar("T", bound=BaseModel)

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """Concrete LLM provider that communicates with a local Ollama server.

    The provider uses a single :class:`httpx.AsyncClient` per instance.
    For request-scoped usage, the caller is responsible for managing the
    client lifecycle (or use the provider as an async context manager).

    Args:
        settings: Application settings used to read Ollama configuration
            (``OLLAMA_BASE_URL``, ``OLLAMA_MODEL``, ``OLLAMA_EMBED_MODEL``).
    """

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        self._embed_model = settings.OLLAMA_EMBED_MODEL
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0),
        )

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a non-streaming text completion via ``POST /api/generate``.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system instruction prepended to the
                generation context.

        Returns:
            The model's response as a plain string.

        Raises:
            :class:`~app.core.exceptions.ExternalServiceError`: If the Ollama
                server is unreachable or returns an unexpected error.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        response = await self._post("/api/generate", payload)
        return str(response.get("response", ""))

    async def extract_structured(
        self,
        prompt: str,
        schema: type[T],
        system_prompt: str = "",
    ) -> T:
        """Extract structured JSON data conforming to *schema*.

        Instructs Ollama to respond in JSON format (``format="json"``),
        appends the JSON schema to the prompt, and validates the response
        using :meth:`pydantic.BaseModel.model_validate_json`.

        Args:
            prompt: The extraction prompt.
            schema: Pydantic model class defining the expected structure.
            system_prompt: Optional system instruction.

        Returns:
            A validated instance of *schema*.

        Raises:
            :class:`~app.core.exceptions.ExternalServiceError`: On connection
                failure.
            :class:`pydantic.ValidationError`: If the model returns JSON that
                does not conform to *schema*.
        """
        schema_json = schema.model_json_schema()
        augmented_prompt = (
            f"{prompt}\n\n"
            f"Respond ONLY with valid JSON conforming to this schema:\n"
            f"{json.dumps(schema_json, indent=2)}"
        )

        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": augmented_prompt,
            "stream": False,
            "format": "json",
        }
        if system_prompt:
            payload["system"] = system_prompt

        response = await self._post("/api/generate", payload)
        raw_json: str = response.get("response", "{}")
        return schema.model_validate_json(raw_json)

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for *text* via ``POST /api/embeddings``.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            :class:`~app.core.exceptions.ExternalServiceError`: On connection
                failure.
        """
        payload: dict[str, Any] = {
            "model": self._embed_model,
            "prompt": text,
        }
        response = await self._post("/api/embeddings", payload)
        embedding: list[float] = response.get("embedding", [])
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts.

        Ollama does not expose a native batch embedding endpoint, so this
        method calls :meth:`embed` sequentially.  Future versions may
        parallelise with :func:`asyncio.gather` when Ollama adds batch
        support.

        Args:
            texts: A list of strings to embed.

        Returns:
            A list of embedding vectors in the same order as *texts*.

        Raises:
            :class:`~app.core.exceptions.ExternalServiceError`: If any
                individual embed call fails.
        """
        results: list[list[float]] = []
        for text in texts:
            embedding = await self.embed(text)
            results.append(embedding)
        return results

    async def health_check(self) -> dict[str, Any]:
        """Verify connectivity to the Ollama server via ``GET /api/tags``.

        Returns:
            A dictionary with ``"status"`` (``"ok"`` or ``"error"``) and
            additional metadata such as available model names.
        """
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            model_names: list[str] = [
                m.get("name", "") for m in data.get("models", [])
            ]
            return {
                "status": "ok",
                "provider": "ollama",
                "base_url": self._base_url,
                "configured_model": self._model,
                "available_models": model_names,
            }
        except httpx.ConnectError as exc:
            logger.warning(
                "ollama_health_check_failed",
                base_url=self._base_url,
                error=str(exc),
            )
            return {
                "status": "error",
                "provider": "ollama",
                "base_url": self._base_url,
                "error": f"Connection refused: {self._base_url}",
            }
        except Exception as exc:
            logger.warning(
                "ollama_health_check_unexpected_error",
                base_url=self._base_url,
                error=str(exc),
            )
            return {
                "status": "error",
                "provider": "ollama",
                "base_url": self._base_url,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST request and return the parsed JSON body.

        Args:
            path: The URL path relative to ``self._base_url``.
            payload: The JSON-serialisable request body.

        Returns:
            The parsed JSON response body as a dictionary.

        Raises:
            :class:`~app.core.exceptions.ExternalServiceError`: On any
                connection error or non-2xx HTTP status.
        """
        try:
            response = await self._client.post(path, json=payload)
            response.raise_for_status()
            return dict(response.json())
        except httpx.ConnectError as exc:
            raise ExternalServiceError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Ensure the Ollama service is running.",
                detail=str(exc),
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(
                f"Ollama returned HTTP {exc.response.status_code}: "
                f"{exc.response.text}",
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise ExternalServiceError(
                f"Unexpected error communicating with Ollama: {exc}",
                detail=str(exc),
            ) from exc
