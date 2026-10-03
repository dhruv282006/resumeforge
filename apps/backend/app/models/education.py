"""Education model definition."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.profile import Profile


class Education(Base):
    """Education record entity attached to a Profile."""

    __tablename__ = "educations"

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
    institution: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    degree: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    field_of_study: Mapped[Optional[str]] = mapped_column(
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
    gpa: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    percentage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
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
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="educations",
    )
