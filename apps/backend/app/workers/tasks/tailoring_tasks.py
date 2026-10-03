"""Celery background tasks for Resume Tailoring and Truth Guard auditing."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict

import structlog
from celery import Task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.job_description import JobDescription
from app.models.profile import Profile
from app.models.resume_version import ResumeVersion
from app.services.tailoring import resume_tailoring_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro):
    """Run an async coroutine synchronously inside a Celery task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="resume.tailor", bind=True)
def tailor_resume_task(
    self: Task,
    resume_version_id: str,
    job_description_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """Background task to run AI Resume Tailoring and Truth Guard verification."""
    logger.info(
        "Starting background resume tailoring task",
        task_id=self.request.id,
        resume_version_id=resume_version_id,
        job_description_id=job_description_id,
    )

    async def _tailor():
        async with AsyncSessionLocal() as session:
            # 1. Fetch ResumeVersion
            stmt_rv = (
                select(ResumeVersion)
                .where(ResumeVersion.id == uuid.UUID(resume_version_id))
            )
            res_rv = await session.execute(stmt_rv)
            rv = res_rv.scalar_one_or_none()
            if not rv:
                return {"status": "FAILED", "error": "Resume version not found"}

            # 2. Fetch JobDescription with requirements & skills
            stmt_jd = (
                select(JobDescription)
                .options(
                    selectinload(JobDescription.requirements),
                    selectinload(JobDescription.skills),
                )
                .where(JobDescription.id == uuid.UUID(job_description_id))
            )
            res_jd = await session.execute(stmt_jd)
            jd = res_jd.scalar_one_or_none()
            if not jd:
                return {"status": "FAILED", "error": "Job description not found"}

            # 3. Fetch Candidate Profile with all evidence collections
            stmt_prof = (
                select(Profile)
                .options(
                    selectinload(Profile.skills),
                    selectinload(Profile.experiences),
                    selectinload(Profile.projects),
                    selectinload(Profile.educations),
                    selectinload(Profile.certifications),
                )
                .where(Profile.user_id == uuid.UUID(user_id))
            )
            res_prof = await session.execute(stmt_prof)
            prof = res_prof.scalar_one_or_none()
            if not prof:
                return {"status": "FAILED", "error": "Candidate profile not found"}

            job = await resume_tailoring_service.create_tailoring_job(
                db=session,
                user_id=uuid.UUID(user_id),
                resume_version=rv,
                job_description=jd,
                profile=prof,
            )

            return {
                "status": job.status,
                "job_id": str(job.id),
                "suggestion_count": len(job.suggestions),
            }

    return _run_async(_tailor())
