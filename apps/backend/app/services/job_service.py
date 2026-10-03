"""Job Description management and matching orchestration service."""

from __future__ import annotations

import uuid
from typing import List, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job_description import JobAnalysis, JobDescription
from app.models.job_match import JobMatch
from app.models.job_requirement import JobRequirement, JobSkillRequirement
from app.models.profile import Profile
from app.models.resume_version import ResumeVersion
from app.schemas.job import JobCreate, JobMatchRequest, JobUpdate
from app.services.jd_analyzer import JobDescriptionAnalyzer
from app.services.matching_engine import MatchingConfig, MatchingEngine, MatchingWeights
from app.services.profile_service import DEFAULT_USER_ID, ProfileService

logger = structlog.get_logger(__name__)


class JobService:
    """Service layer for job descriptions, analysis, and semantic matching."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.analyzer = JobDescriptionAnalyzer(session)
        self.matching_engine = MatchingEngine(session)
        self.profile_service = ProfileService(session)

    # ---------------- Job CRUD ----------------
    async def create_job(
        self,
        payload: JobCreate,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> JobDescription:
        """Create a new job description."""
        job = JobDescription(
            user_id=user_id,
            title=payload.title,
            company=payload.company,
            location=payload.location,
            employment_type=payload.employment_type,
            source_url=payload.source_url,
            raw_text=payload.raw_text,
            status="DRAFT",
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return await self.get_job(job.id, user_id) or job

    async def get_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[JobDescription]:
        """Fetch job description with requirements, skills, and analysis."""
        stmt = (
            select(JobDescription)
            .where(JobDescription.id == job_id, JobDescription.user_id == user_id)
            .options(
                selectinload(JobDescription.analysis),
                selectinload(JobDescription.requirements),
                selectinload(JobDescription.skills),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_jobs(
        self,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> List[JobDescription]:
        """List all job descriptions for a user."""
        stmt = (
            select(JobDescription)
            .where(JobDescription.user_id == user_id)
            .options(
                selectinload(JobDescription.analysis),
                selectinload(JobDescription.requirements),
                selectinload(JobDescription.skills),
            )
            .order_by(JobDescription.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_job(
        self,
        job_id: uuid.UUID,
        payload: JobUpdate,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[JobDescription]:
        """Update an existing job description."""
        job = await self.get_job(job_id, user_id)
        if not job:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(job, key, value)

        await self.session.commit()
        return await self.get_job(job_id, user_id)

    async def delete_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> bool:
        """Delete a job description and all associated requirements and matches."""
        job = await self.get_job(job_id, user_id)
        if not job:
            return False

        await self.session.delete(job)
        await self.session.commit()
        return True

    # ---------------- Job Analysis ----------------
    async def analyze_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[JobAnalysis]:
        """Trigger analysis pipeline on a JobDescription."""
        job = await self.get_job(job_id, user_id)
        if not job:
            return None

        analysis = await self.analyzer.analyze_job(job)
        return analysis

    async def get_analysis(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[JobAnalysis]:
        """Retrieve latest analysis for a JobDescription."""
        job = await self.get_job(job_id, user_id)
        if not job:
            return None
        return job.analysis

    async def get_requirements(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
        category: Optional[str] = None,
        importance: Optional[str] = None,
    ) -> List[JobRequirement]:
        """List extracted requirements with optional filters."""
        stmt = select(JobRequirement).where(JobRequirement.job_id == job_id)
        if category:
            stmt = stmt.where(JobRequirement.category == category.upper())
        if importance:
            stmt = stmt.where(JobRequirement.importance == importance.upper())
        stmt = stmt.order_by(JobRequirement.created_at)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Semantic Matching ----------------
    async def match_job(
        self,
        job_id: uuid.UUID,
        payload: JobMatchRequest,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[JobMatch]:
        """Run hybrid semantic matching against Profile or Resume Version."""
        job = await self.get_job(job_id, user_id)
        if not job:
            return None

        # Ensure job has requirements extracted
        if not job.requirements:
            await self.analyzer.analyze_job(job)
            job = await self.get_job(job_id, user_id)

        # Get profile
        profile = await self.profile_service.get_or_create_profile(user_id)

        # Optional Resume Version
        resume_version: Optional[ResumeVersion] = None
        if payload.target_type == "RESUME_VERSION" and payload.resume_version_id:
            rv_stmt = select(ResumeVersion).where(ResumeVersion.id == payload.resume_version_id)
            rv_res = await self.session.execute(rv_stmt)
            resume_version = rv_res.scalars().first()

        # Custom weights if provided
        custom_weights: Optional[MatchingWeights] = None
        if payload.weights:
            custom_weights = MatchingWeights(
                required_skills=payload.weights.required_skills,
                preferred_skills=payload.weights.preferred_skills,
                experience_relevance=payload.weights.experience_relevance,
                project_relevance=payload.weights.project_relevance,
                semantic_alignment=payload.weights.semantic_alignment,
            )

        match = await self.matching_engine.compute_match(
            job=job,
            profile=profile,
            resume_version=resume_version,
            custom_weights=custom_weights,
        )
        return await self.get_match(job_id, match.id, user_id)

    async def get_match(
        self,
        job_id: uuid.UUID,
        match_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[JobMatch]:
        """Retrieve match detail with all item evidence breakdowns."""
        stmt = (
            select(JobMatch)
            .where(
                JobMatch.id == match_id,
                JobMatch.job_id == job_id,
                JobMatch.user_id == user_id,
            )
            .options(
                selectinload(JobMatch.items),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_matches(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> List[JobMatch]:
        """List match history for a job."""
        stmt = (
            select(JobMatch)
            .where(
                JobMatch.job_id == job_id,
                JobMatch.user_id == user_id,
            )
            .options(
                selectinload(JobMatch.items),
            )
            .order_by(JobMatch.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

