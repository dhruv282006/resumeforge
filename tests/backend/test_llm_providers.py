"""Tests for the LLM provider abstraction layer.

These tests verify:
1. The factory function returns the correct provider for each LLM_PROVIDER value.
2. Placeholder providers raise NotImplementedError for generative methods.
3. OllamaProvider.health_check() handles connection failures gracefully.

No real LLM connections are made — httpx is mocked throughout.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


class TestGetLlmProviderFactory:
    """Verify get_llm_provider() returns the correct provider implementation."""

    def test_returns_ollama_provider_by_default(self, settings) -> None:
        """get_llm_provider returns OllamaProvider when LLM_PROVIDER='ollama'."""
        from app.ai.providers.base import get_llm_provider
        from app.ai.providers.ollama import OllamaProvider

        # Settings fixture has LLM_PROVIDER defaulting to 'ollama'
        provider = get_llm_provider(settings)
        assert isinstance(provider, OllamaProvider)

    def test_returns_openai_provider(self) -> None:
        """get_llm_provider returns OpenAIProvider when LLM_PROVIDER='openai'."""
        from app.ai.providers.base import get_llm_provider
        from app.ai.providers.openai import OpenAIProvider
        from app.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_EMBED_MODEL = "text-embedding-3-small"

        provider = get_llm_provider(mock_settings)
        assert isinstance(provider, OpenAIProvider)

    def test_returns_gemini_provider(self) -> None:
        """get_llm_provider returns GeminiProvider when LLM_PROVIDER='gemini'."""
        from app.ai.providers.base import get_llm_provider
        from app.ai.providers.gemini import GeminiProvider
        from app.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.GEMINI_MODEL = "gemini-1.5-pro"
        mock_settings.GEMINI_EMBED_MODEL = "text-embedding-004"

        provider = get_llm_provider(mock_settings)
        assert isinstance(provider, GeminiProvider)

    def test_raises_value_error_for_unknown_provider(self) -> None:
        """get_llm_provider raises ValueError for an unknown provider name."""
        from app.ai.providers.base import get_llm_provider
        from app.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.LLM_PROVIDER = "unknown_llm"

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider(mock_settings)


class TestOpenAIProviderPlaceholder:
    """Verify OpenAIProvider raises NotImplementedError for generative methods."""

    def _make_provider(self):
        from app.ai.providers.openai import OpenAIProvider
        from app.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_EMBED_MODEL = "text-embedding-3-small"
        return OpenAIProvider(settings=mock_settings)

    @pytest.mark.asyncio
    async def test_complete_raises_not_implemented(self) -> None:
        """complete() raises NotImplementedError."""
        provider = self._make_provider()
        with pytest.raises(NotImplementedError, match="OpenAI"):
            await provider.complete("hello")

    @pytest.mark.asyncio
    async def test_embed_raises_not_implemented(self) -> None:
        """embed() raises NotImplementedError."""
        provider = self._make_provider()
        with pytest.raises(NotImplementedError, match="OpenAI"):
            await provider.embed("hello")

    @pytest.mark.asyncio
    async def test_embed_batch_raises_not_implemented(self) -> None:
        """embed_batch() raises NotImplementedError."""
        provider = self._make_provider()
        with pytest.raises(NotImplementedError, match="OpenAI"):
            await provider.embed_batch(["hello", "world"])

    @pytest.mark.asyncio
    async def test_health_check_returns_not_implemented_dict(self) -> None:
        """health_check() returns a structured 'not_implemented' dict."""
        provider = self._make_provider()
        result = await provider.health_check()
        assert result["status"] == "not_implemented"
        assert result["provider"] == "openai"


class TestGeminiProviderPlaceholder:
    """Verify GeminiProvider raises NotImplementedError for generative methods."""

    def _make_provider(self):
        from app.ai.providers.gemini import GeminiProvider
        from app.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.GEMINI_MODEL = "gemini-1.5-pro"
        mock_settings.GEMINI_EMBED_MODEL = "text-embedding-004"
        return GeminiProvider(settings=mock_settings)

    @pytest.mark.asyncio
    async def test_complete_raises_not_implemented(self) -> None:
        """complete() raises NotImplementedError."""
        provider = self._make_provider()
        with pytest.raises(NotImplementedError, match="Gemini"):
            await provider.complete("hello")

    @pytest.mark.asyncio
    async def test_embed_raises_not_implemented(self) -> None:
        """embed() raises NotImplementedError."""
        provider = self._make_provider()
        with pytest.raises(NotImplementedError, match="Gemini"):
            await provider.embed("hello")

    @pytest.mark.asyncio
    async def test_health_check_returns_not_implemented_dict(self) -> None:
        """health_check() returns a structured 'not_implemented' dict."""
        provider = self._make_provider()
        result = await provider.health_check()
        assert result["status"] == "not_implemented"
        assert result["provider"] == "gemini"


class TestOllamaProviderHealthCheck:
    """Verify OllamaProvider.health_check() handles connectivity failures."""

    def _make_provider(self, base_url: str = "http://ollama:11434"):
        from app.ai.providers.ollama import OllamaProvider
        from app.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.OLLAMA_BASE_URL = base_url
        mock_settings.OLLAMA_MODEL = "llama3.1:8b"
        mock_settings.OLLAMA_EMBED_MODEL = "nomic-embed-text"
        return OllamaProvider(settings=mock_settings)

    @pytest.mark.asyncio
    async def test_health_check_returns_error_dict_on_connect_error(self) -> None:
        """health_check() returns an error dict (not raises) when Ollama is down."""
        provider = self._make_provider()

        with patch.object(
            provider._client,
            "get",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await provider.health_check()

        assert result["status"] == "error"
        assert result["provider"] == "ollama"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check_returns_ok_on_success(self) -> None:
        """health_check() returns status 'ok' when Ollama responds."""
        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3.1:8b"}, {"name": "nomic-embed-text"}]
        }

        with patch.object(provider._client, "get", AsyncMock(return_value=mock_response)):
            result = await provider.health_check()

        assert result["status"] == "ok"
        assert result["provider"] == "ollama"
        assert "llama3.1:8b" in result["available_models"]

    @pytest.mark.asyncio
    async def test_complete_raises_external_service_error_on_connect_failure(
        self,
    ) -> None:
        """complete() raises ExternalServiceError when Ollama cannot be reached."""
        from app.core.exceptions import ExternalServiceError

        provider = self._make_provider()

        with patch.object(
            provider._client,
            "post",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with pytest.raises(ExternalServiceError, match="Cannot connect to Ollama"):
                await provider.complete("test prompt")
