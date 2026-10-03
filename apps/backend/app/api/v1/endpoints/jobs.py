"""Endpoints for Job Description management, AI analysis, and semantic matching."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.job import (
    JobAnalysisResponse,
    JobCreate,
    JobMatchRequest,
    JobMatchResponse,
    JobRequirementResponse,
    JobResponse,
    JobUpdate,
)
from app.services.job_service import DEFAULT_USER_ID, JobService
from app.workers.tasks.job_tasks import analyze_job_task, match_job_task

router = APIRouter()


def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


# ---------------- Job CRUD ----------------
@router.get("", response_model=List[JobResponse])
async def list_jobs(
    service: JobService = Depends(get_job_service),
) -> List[JobResponse]:
    """List all candidate job descriptions."""
    return await service.list_jobs(DEFAULT_USER_ID)  # type: ignore[return-value]


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Create a new Job Description."""
    return await service.create_job(payload, DEFAULT_USER_ID)  # type: ignore[return-value]


@router.get("/{id}", response_model=JobResponse)
async def get_job(
    id: uuid.UUID,
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Get Job Description details, requirements, and analysis."""
    job = await service.get_job(id, DEFAULT_USER_ID)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return job  # type: ignore[return-value]


@router.put("/{id}", response_model=JobResponse)
async def update_job(
    id: uuid.UUID,
    payload: JobUpdate,
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Update job description fields."""
    job = await service.update_job(id, payload, DEFAULT_USER_ID)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return job  # type: ignore[return-value]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_job(
    id: uuid.UUID,
    service: JobService = Depends(get_job_service),
) -> None:
    """Delete job description and all associated requirements and matches."""
    deleted = await service.delete_job(id, DEFAULT_USER_ID)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")


# ---------------- Job Analysis ----------------
@router.post("/{id}/analyze", response_model=JobAnalysisResponse)
async def analyze_job(
    id: uuid.UUID,
    async_mode: bool = Query(False, description="Dispatch as background Celery task"),
    service: JobService = Depends(get_job_service),
) -> JobAnalysisResponse:
    """Trigger job description parsing and requirement extraction."""
    job = await service.get_job(id, DEFAULT_USER_ID)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    if async_mode:
        task = analyze_job_task.delay(str(id), str(DEFAULT_USER_ID))
        # Return pending analysis object with task info
        return JobAnalysisResponse(
            id=uuid.uuid4(),
            job_id=id,
            status="QUEUED",
            summary=f"Analysis task dispatched: {task.id}",
            total_requirements=0,
            total_skills=0,
            raw_analysis_json={"task_id": task.id},
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    # Synchronous execution
    analysis = await service.analyze_job(id, DEFAULT_USER_ID)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to analyze job description")
    return analysis  # type: ignore[return-value]


@router.get("/{id}/analysis", response_model=JobAnalysisResponse)
async def get_job_analysis(
    id: uuid.UUID,
    service: JobService = Depends(get_job_service),
) -> JobAnalysisResponse:
    """Retrieve structured analysis for a job description."""
    analysis = await service.get_analysis(id, DEFAULT_USER_ID)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis found for this job")
    return analysis  # type: ignore[return-value]


@router.get("/{id}/requirements", response_model=List[JobRequirementResponse])
async def list_job_requirements(
    id: uuid.UUID,
    category: Optional[str] = Query(None, description="Filter by category (SKILL, EXPERIENCE, etc.)"),
    importance: Optional[str] = Query(None, description="Filter by importance (REQUIRED, PREFERRED)"),
    service: JobService = Depends(get_job_service),
) -> List[JobRequirementResponse]:
    """List extracted requirements for a job description."""
    requirements = await service.get_requirements(
        job_id=id,
        user_id=DEFAULT_USER_ID,
        category=category,
        importance=importance,
    )
    return requirements  # type: ignore[return-value]


# ---------------- Matching ----------------
@router.post("/{id}/match", response_model=JobMatchResponse)
async def match_job(
    id: uuid.UUID,
    payload: JobMatchRequest,
    async_mode: bool = Query(False, description="Dispatch as background Celery task"),
    service: JobService = Depends(get_job_service),
) -> JobMatchResponse:
    """Run semantic matching against candidate Master Profile or a specific Resume Version."""
    job = await service.get_job(id, DEFAULT_USER_ID)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    if async_mode:
        task = match_job_task.delay(str(id), payload.model_dump(), str(DEFAULT_USER_ID))
        return JobMatchResponse(
            id=uuid.uuid4(),
            job_id=id,
            user_id=DEFAULT_USER_ID,
            profile_id=uuid.uuid4(),
            target_type=payload.target_type,
            overall_score=0.0,
            breakdown_scores={},
            score_weights={},
            status="QUEUED",
            error_detail=f"Match task dispatched: {task.id}",
            created_at=job.created_at,
            updated_at=job.updated_at,
            items=[],
        )

    # Synchronous execution
    match = await service.match_job(id, payload, DEFAULT_USER_ID)
    if not match:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to compute match")
    return match  # type: ignore[return-value]


@router.get("/{id}/matches", response_model=List[JobMatchResponse])
async def list_job_matches(
    id: uuid.UUID,
    service: JobService = Depends(get_job_service),
) -> List[JobMatchResponse]:
    """List match history for a job description."""
    matches = await service.list_matches(id, DEFAULT_USER_ID)
    return matches  # type: ignore[return-value]


@router.get("/{id}/matches/{match_id}", response_model=JobMatchResponse)
async def get_job_match(
    id: uuid.UUID,
    match_id: uuid.UUID,
    service: JobService = Depends(get_job_service),
) -> JobMatchResponse:
    """Get detailed match results, component scores, and requirement evidence breakdown."""
    match = await service.get_match(id, match_id, DEFAULT_USER_ID)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match record not found")
    return match  # type: ignore[return-value]

