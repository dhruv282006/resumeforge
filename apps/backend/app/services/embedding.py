"""Embedding provider abstraction and vector service."""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List, Optional

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.embedding import EMBEDDING_DIM, EmbeddingRecord

logger = structlog.get_logger(__name__)


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text for caching/reuse."""
    normalized = " ".join(text.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


class EmbeddingProvider(ABC):
    """Abstract interface for dense text embedding models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the embedding model."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the embedding vectors."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""


class FallbackEmbeddingProvider(EmbeddingProvider):
    """Deterministic, offline embedding provider using character n-gram projection.

    Guarantees reproducible, unit-norm float vectors (dimension 768)
    even when Ollama or external models are completely offline.
    """

    def __init__(self, dimension: int = EMBEDDING_DIM) -> None:
        self._dim = dimension

    @property
    def model_name(self) -> str:
        return "deterministic-fallback"

    @property
    def dimension(self) -> int:
        return self._dim

    def _generate_vector(self, text: str) -> List[float]:
        """Generate normalized pseudo-semantic vector from token n-grams."""
        if not text or not text.strip():
            return [0.0] * self._dim

        vec = [0.0] * self._dim
        words = text.lower().strip().split()
        for word in words:
            # Word hash bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h >> 4) % 2 == 0 else -1.0
            vec[idx] += sign * 1.0

            # Substring trigrams
            for i in range(len(word) - 2):
                tri = word[i : i + 3]
                th = int(hashlib.sha1(tri.encode("utf-8")).hexdigest(), 16)
                tidx = th % self._dim
                tsign = 1.0 if (th >> 3) % 2 == 0 else -1.0
                vec[tidx] += tsign * 0.5

        # Normalize to unit length (L2 norm)
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama-backed dense embedding provider."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        dimension: int = EMBEDDING_DIM,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model_name or settings.OLLAMA_EMBED_MODEL
        self._dim = dimension
        self._fallback = FallbackEmbeddingProvider(dimension=dimension)
        self._is_online: Optional[bool] = None

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_text(self, text: str) -> List[float]:
        """Embed single text via Ollama /api/embeddings with fallback on failure."""
        if self._is_online is False:
            return await self._fallback.embed_text(text)

        try:
            timeout = httpx.Timeout(5.0, connect=0.3)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": text},
                )
                if res.status_code == 200:
                    self._is_online = True
                    raw_emb = res.json().get("embedding", [])
                    if raw_emb:
                        # Pad or truncate to self._dim if necessary
                        if len(raw_emb) < self._dim:
                            raw_emb = raw_emb + [0.0] * (self._dim - len(raw_emb))
                        return raw_emb[: self._dim]
                else:
                    self._is_online = False
        except Exception as exc:
            self._is_online = False
            logger.info(
                "Ollama embedding unavailable, falling back to deterministic provider",
                error=str(exc),
            )

        # Fallback if Ollama unreachable
        return await self._fallback.embed_text(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]


def get_embedding_provider() -> EmbeddingProvider:
    """Factory creating the default embedding provider (Ollama with automatic offline fallback)."""
    return OllamaEmbeddingProvider()


class EmbeddingService:
    """High-level service managing vector generation, caching, and persistence."""

    def __init__(
        self,
        session: AsyncSession,
        provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.session = session
        self.provider = provider or get_embedding_provider()

    async def get_or_create_embedding(
        self,
        source_type: str,
        source_id: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> List[float]:
        """Fetch cached embedding from database or compute and persist a new one."""
        text_hash = compute_text_hash(text)

        # 1. Check cache by text_hash and model_name
        stmt = select(EmbeddingRecord).where(
            EmbeddingRecord.text_hash == text_hash,
            EmbeddingRecord.model_name == self.provider.model_name,
        )
        result = await self.session.execute(stmt)
        cached = result.scalars().first()
        if cached:
            return list(cached.embedding)

        # 2. Compute embedding
        vector = await self.provider.embed_text(text)

        # 3. Persist embedding record
        record = EmbeddingRecord(
            source_type=source_type,
            source_id=str(source_id),
            chunk_text=text,
            text_hash=text_hash,
            embedding=vector,
            model_name=self.provider.model_name,
            embedding_dim=self.provider.dimension,
            metadata_json=metadata or {},
        )
        self.session.add(record)
        await self.session.commit()
        return vector

