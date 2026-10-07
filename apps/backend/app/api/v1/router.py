"""V1 API router — aggregates all versioned endpoint routers.

Add new feature routers here as they are developed, keeping this file
as the single registration point for /api/v1/* routes.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    applications,
    auth,
    health,
    jobs,
    profile,
    resumes,
    tailoring,
    tasks,
)

api_v1_router = APIRouter()

# Health check — no auth required
api_v1_router.include_router(
    health.router,
    tags=["Health"],
)

# Authentication & User Management
api_v1_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
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

# Resume Tailoring, Truth Guard & Diffing
api_v1_router.include_router(
    tailoring.router,
    prefix="/resumes",
    tags=["Tailoring"],
)

# Job Descriptions and Semantic Matching
api_v1_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["Jobs"],
)

# Applications Tracking
api_v1_router.include_router(
    applications.router,
    prefix="/applications",
    tags=["Applications"],
)

# Background Tasks
api_v1_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"],
)

