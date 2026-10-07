"""Endpoints for Job Applications tracking."""

from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatsResponse,
    ApplicationUpdate,
)
from app.services.application_service import DEFAULT_USER_ID, ApplicationService

router = APIRouter()


def get_application_service(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(db)


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by status (APPLIED, INTERVIEWING, OFFERED, REJECTED)"),
    service: ApplicationService = Depends(get_application_service),
) -> List[ApplicationResponse]:
    """List candidate job applications."""
    return await service.list_applications(DEFAULT_USER_ID, status=status)  # type: ignore[return-value]


@router.get("/stats", response_model=ApplicationStatsResponse)
async def get_application_stats(
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationStatsResponse:
    """Get aggregate funnel statistics of applications."""
    return await service.get_stats(DEFAULT_USER_ID)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    """Log a new job application."""
    return await service.create_application(payload, DEFAULT_USER_ID)  # type: ignore[return-value]


@router.get("/{id}", response_model=ApplicationResponse)
async def get_application(
    id: uuid.UUID,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    """Get details of a single application."""
    app = await service.get_application(id, DEFAULT_USER_ID)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return app  # type: ignore[return-value]


@router.put("/{id}", response_model=ApplicationResponse)
@router.patch("/{id}", response_model=ApplicationResponse)
async def update_application(
    id: uuid.UUID,
    payload: ApplicationUpdate,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    """Update fields or stage of an application."""
    app = await service.update_application(id, payload, DEFAULT_USER_ID)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return app  # type: ignore[return-value]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_application(
    id: uuid.UUID,
    service: ApplicationService = Depends(get_application_service),
) -> None:
    """Delete an application."""
    deleted = await service.delete_application(id, DEFAULT_USER_ID)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
