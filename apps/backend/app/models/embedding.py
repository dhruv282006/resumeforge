"""EmbeddingRecord model with pgvector support."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

EMBEDDING_DIM = 768


class EmbeddingRecord(Base):
    """Vector embedding record for semantic search and retrieval grounding."""

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # JOB_REQUIREMENT, PROFILE_SKILL, PROFILE_EXPERIENCE, PROFILE_PROJECT, PROFILE_EDUCATION, RESUME_CHUNK
    source_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    text_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )  # SHA-256 hash for deduplication/caching
    embedding: Mapped[List[float]] = mapped_column(
        Vector(EMBEDDING_DIM),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        default="nomic-embed-text",
        nullable=False,
    )
    embedding_dim: Mapped[int] = mapped_column(
        Integer,
        default=EMBEDDING_DIM,
        nullable=False,
    )
    metadata_json: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_embeddings_source_hash", "source_type", "text_hash"),
        Index("ix_embeddings_model_hash", "model_name", "text_hash"),
    )

