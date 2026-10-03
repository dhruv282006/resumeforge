"""Celery background tasks for Job Description analysis and semantic matching."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict

import structlog
from celery import Task

from app.core.database import AsyncSessionLocal
from app.schemas.job import JobMatchRequest
from app.services.job_service import JobService
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


@celery_app.task(name="job.analyze", bind=True)
def analyze_job_task(self: Task, job_id: str, user_id: str) -> Dict[str, Any]:
    """Background task to run JD parsing and requirement extraction."""
    logger.info("Starting background job analysis task", task_id=self.request.id, job_id=job_id)

    async def _analyze():
        async with AsyncSessionLocal() as session:
            service = JobService(session)
            analysis = await service.analyze_job(uuid.UUID(job_id), uuid.UUID(user_id))
            if not analysis:
                return {"status": "FAILED", "job_id": job_id, "error": "Job not found"}
            return {
                "status": analysis.status,
                "job_id": job_id,
                "total_requirements": analysis.total_requirements,
                "total_skills": analysis.total_skills,
            }

    return _run_async(_analyze())


@celery_app.task(name="job.match", bind=True)
def match_job_task(self: Task, job_id: str, payload_dict: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Background task to run candidate evidence embedding and semantic matching."""
    logger.info("Starting background job match task", task_id=self.request.id, job_id=job_id)

    async def _match():
        async with AsyncSessionLocal() as session:
            service = JobService(session)
            req = JobMatchRequest(**payload_dict)
            match = await service.match_job(uuid.UUID(job_id), req, uuid.UUID(user_id))
            if not match:
                return {"status": "FAILED", "job_id": job_id, "error": "Job or Profile not found"}
            return {
                "status": match.status,
                "job_id": job_id,
                "match_id": str(match.id),
                "overall_score": match.overall_score,
                "breakdown": match.breakdown_scores,
            }

    return _run_async(_match())
