"""JobDescription and JobAnalysis models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job_match import JobMatch
    from app.models.job_requirement import JobRequirement, JobSkillRequirement
    from app.models.user import User


class JobDescription(Base):
    """Job Description posted or pasted by user for analysis and matching."""

    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    company: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    employment_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    raw_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    normalized_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="DRAFT",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="job_descriptions",
    )
    requirements: Mapped[List[JobRequirement]] = relationship(
        "JobRequirement",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="JobRequirement.created_at",
    )
    skills: Mapped[List[JobSkillRequirement]] = relationship(
        "JobSkillRequirement",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    analysis: Mapped[Optional[JobAnalysis]] = relationship(
        "JobAnalysis",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )
    matches: Mapped[List[JobMatch]] = relationship(
        "JobMatch",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="desc(JobMatch.created_at)",
    )


class JobAnalysis(Base):
    """Structured analysis metadata and summary for a Job Description."""

    __tablename__ = "job_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    total_requirements: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_skills: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    raw_analysis_json: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    job: Mapped[JobDescription] = relationship(
        "JobDescription",
        back_populates="analysis",
    )

