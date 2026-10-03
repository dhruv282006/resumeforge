"""Profile model definition."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.certification import Certification
    from app.models.education import Education
    from app.models.experience import Experience
    from app.models.project import Project
    from app.models.skill import Skill
    from app.models.user import User


class Profile(Base):
    """User profile entity storing master career data."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    headline: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    linkedin_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    github_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    portfolio_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    preferred_roles: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    preferred_industries: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    preferred_locations: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    years_of_experience: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    current_status: Mapped[Optional[str]] = mapped_column(
        String(100),
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )
    educations: Mapped[List["Education"]] = relationship(
        "Education",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    experiences: Mapped[List["Experience"]] = relationship(
        "Experience",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    skills: Mapped[List["Skill"]] = relationship(
        "Skill",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    certifications: Mapped[List["Certification"]] = relationship(
        "Certification",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
