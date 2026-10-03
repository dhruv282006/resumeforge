"""JobRequirement and JobSkillRequirement models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job_description import JobDescription
    from app.models.job_match import JobMatchItem


class JobRequirement(Base):
    """Individual extracted requirement from a job description."""

    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default="OTHER",
        nullable=False,
    )  # SKILL, EXPERIENCE, EDUCATION, RESPONSIBILITY, CERTIFICATION, DOMAIN_KNOWLEDGE, OTHER
    importance: Mapped[str] = mapped_column(
        String(50),
        default="UNKNOWN",
        nullable=False,
    )  # REQUIRED, PREFERRED, OPTIONAL, UNKNOWN
    extracted_skill: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    min_experience_years: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    source_section: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    job: Mapped[JobDescription] = relationship(
        "JobDescription",
        back_populates="requirements",
    )
    match_items: Mapped[List[JobMatchItem]] = relationship(
        "JobMatchItem",
        back_populates="requirement",
        cascade="all, delete-orphan",
    )
    skills: Mapped[List[JobSkillRequirement]] = relationship(
        "JobSkillRequirement",
        back_populates="requirement",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_job_requirements_job_cat", "job_id", "category"),
        Index("ix_job_requirements_job_imp", "job_id", "importance"),
    )


class JobSkillRequirement(Base):
    """Normalized skill requirement extracted from a job description."""

    __tablename__ = "job_skill_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    normalized_skill: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )  # TECHNICAL, SOFT, TOOL, DOMAIN
    importance: Mapped[str] = mapped_column(
        String(50),
        default="REQUIRED",
        nullable=False,
    )  # REQUIRED, PREFERRED, OPTIONAL
    min_years: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    job: Mapped[JobDescription] = relationship(
        "JobDescription",
        back_populates="skills",
    )
    requirement: Mapped[Optional[JobRequirement]] = relationship(
        "JobRequirement",
        back_populates="skills",
    )

