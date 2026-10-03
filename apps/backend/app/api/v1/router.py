"""V1 API router — aggregates all versioned endpoint routers.

Add new feature routers here as they are developed, keeping this file
as the single registration point for /api/v1/* routes.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health, jobs, profile, resumes, tasks

api_v1_router = APIRouter()

# Health check — no auth required
api_v1_router.include_router(
    health.router,
    tags=["Health"],
)

# Master Career Profile and sub-entities
api_v1_router.include_router(
    profile.router,
    prefix="/profile",
    tags=["Profile"],
)

# Resumes and version control
api_v1_router.include_router(
    resumes.router,
    prefix="/resumes",
    tags=["Resumes"],
)

# Job Descriptions and Semantic Matching
api_v1_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["Jobs"],
)

# Background Tasks
api_v1_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"],
)

