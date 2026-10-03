"""JobMatch and JobMatchItem models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job_description import JobDescription
    from app.models.job_requirement import JobRequirement
    from app.models.profile import Profile
    from app.models.resume_version import ResumeVersion
    from app.models.user import User


class JobMatch(Base):
    """Job-to-Candidate matching analysis record with breakdown scores and weights."""

    __tablename__ = "job_matches"

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
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    resume_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(50),
        default="PROFILE",
        nullable=False,
    )  # PROFILE, RESUME_VERSION
    overall_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )  # 0 to 100
    breakdown_scores: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )  # {"required_skills": 88.0, "preferred_skills": 72.0, "experience_relevance": 81.0, ...}
    score_weights: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )  # Persisted scoring weights for reproducibility
    status: Mapped[str] = mapped_column(
        String(50),
        default="COMPLETED",
        nullable=False,
    )  # PENDING, PROCESSING, COMPLETED, FAILED
    error_detail: Mapped[Optional[str]] = mapped_column(
        Text,
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

    # Relationships
    job: Mapped[JobDescription] = relationship(
        "JobDescription",
        back_populates="matches",
    )
    profile: Mapped[Profile] = relationship("Profile")
    resume_version: Mapped[Optional[ResumeVersion]] = relationship("ResumeVersion")
    items: Mapped[List[JobMatchItem]] = relationship(
        "JobMatchItem",
        back_populates="job_match",
        cascade="all, delete-orphan",
        order_by="JobMatchItem.created_at",
    )


class JobMatchItem(Base):
    """Detailed evidence-based match for an individual requirement."""

    __tablename__ = "job_match_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_matches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_requirements.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # MATCHED, PARTIAL, MISSING, UNKNOWN
    score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    matched_entity_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # SKILL, EXPERIENCE, PROJECT, EDUCATION, CERTIFICATION, RESUME_TEXT, NONE
    matched_entity_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    matched_entity_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    evidence_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    evidence_source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # USER_PROVIDED, RESUME_PARSED, AI_INFERRED, IMPORTED, NONE
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    job_match: Mapped[JobMatch] = relationship(
        "JobMatch",
        back_populates="items",
    )
    requirement: Mapped[JobRequirement] = relationship(
        "JobRequirement",
        back_populates="match_items",
    )

    __table_args__ = (
        Index("ix_job_match_items_match_status", "job_match_id", "status"),
    )

