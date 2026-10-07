"""Application tracking service."""

from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationStatsResponse, ApplicationUpdate

DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class ApplicationService:
    """Handles candidate job application lifecycle and statistics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _ensure_user(self, user_id: uuid.UUID) -> None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            user = User(
                id=user_id,
                email="candidate@resumeforge.local",
                full_name="Candidate User",
                role="CANDIDATE",
                is_active=True,
            )
            self.db.add(user)
            await self.db.commit()

    async def list_applications(
        self,
        user_id: uuid.UUID = DEFAULT_USER_ID,
        status: Optional[str] = None,
    ) -> List[Application]:
        """List all applications for user, optionally filtered by status."""
        await self._ensure_user(user_id)
        stmt = (
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
        )
        if status:
            stmt = stmt.where(Application.status == status.upper())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_application(
        self,
        application_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[Application]:
        """Get single application by ID owned by user."""
        stmt = select(Application).where(
            Application.id == application_id, Application.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_application(
        self,
        data: ApplicationCreate,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Application:
        """Log a new job application."""
        await self._ensure_user(user_id)
        app = Application(
            user_id=user_id,
            company=data.company,
            position=data.position,
            status=data.status.upper() if data.status else "APPLIED",
            location=data.location,
            salary_range=data.salary_range,
            job_url=data.job_url,
            applied_date=data.applied_date,
            notes=data.notes,
            job_id=data.job_id,
            resume_id=data.resume_id,
            resume_version_id=data.resume_version_id,
        )
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def update_application(
        self,
        application_id: uuid.UUID,
        data: ApplicationUpdate,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[Application]:
        """Update fields or stage of an application."""
        app = await self.get_application(application_id, user_id)
        if not app:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == "status" and value:
                value = value.upper()
            setattr(app, key, value)

        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def delete_application(
        self,
        application_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> bool:
        """Delete an application."""
        app = await self.get_application(application_id, user_id)
        if not app:
            return False

        await self.db.delete(app)
        await self.db.commit()
        return True

    async def get_stats(
        self,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> ApplicationStatsResponse:
        """Compute application funnel statistics."""
        apps = await self.list_applications(user_id)
        counts = {
            "total": len(apps),
            "applied": 0,
            "screening": 0,
            "interviewing": 0,
            "offered": 0,
            "rejected": 0,
            "withdrawn": 0,
        }
        for a in apps:
            st = a.status.lower()
            if st in counts:
                counts[st] += 1
            elif st == "applied":
                counts["applied"] += 1

        return ApplicationStatsResponse(**counts)
