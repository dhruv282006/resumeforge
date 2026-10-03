"""Project model definition."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.profile import Profile


class Project(Base):
    """Project entity attached to a Profile."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    technologies: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    role: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    start_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    end_date: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    project_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    github_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    achievements: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    metrics: Mapped[Optional[Any]] = mapped_column(
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

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="projects",
    )
