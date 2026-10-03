"""Endpoints for Resume management and version control."""

from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.resume import (
    ResumeCreate,
    ResumeResponse,
    ResumeUpdate,
    ResumeVersionClone,
    ResumeVersionCreate,
    ResumeVersionResponse,
)
from app.services.resume_service import DEFAULT_USER_ID, ResumeService

router = APIRouter()


def get_resume_service(db: AsyncSession = Depends(get_db)) -> ResumeService:
    return ResumeService(db)


# ---------------- Resume Document Endpoints ----------------
@router.get("", response_model=List[ResumeResponse])
async def list_resumes(
    service: ResumeService = Depends(get_resume_service),
) -> List[ResumeResponse]:
    """List all resume families owned by candidate."""
    return await service.list_resumes(DEFAULT_USER_ID)  # type: ignore[return-value]


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    payload: ResumeCreate,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    """Create a new Resume family with initial version."""
    return await service.create_resume(payload, DEFAULT_USER_ID)  # type: ignore[return-value]


@router.get("/{id}", response_model=ResumeResponse)
async def get_resume(
    id: uuid.UUID,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    """Get single resume with its complete version tree."""
    resume = await service.get_resume(id, DEFAULT_USER_ID)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume  # type: ignore[return-value]


@router.put("/{id}", response_model=ResumeResponse)
async def update_resume(
    id: uuid.UUID,
    payload: ResumeUpdate,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    """Update resume metadata or active version."""
    resume = await service.update_resume(id, payload, DEFAULT_USER_ID)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume  # type: ignore[return-value]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_resume(
    id: uuid.UUID,
    service: ResumeService = Depends(get_resume_service),
) -> None:
    """Delete resume and all its version snapshots and associated files."""
    deleted = await service.delete_resume(id, DEFAULT_USER_ID)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")


# ---------------- Version Control Endpoints ----------------
@router.get("/{id}/versions", response_model=List[ResumeVersionResponse])
async def list_resume_versions(
    id: uuid.UUID,
    service: ResumeService = Depends(get_resume_service),
) -> List[ResumeVersionResponse]:
    """List all versions of a specific resume."""
    versions = await service.list_versions(id, DEFAULT_USER_ID)
    return versions  # type: ignore[return-value]


@router.post("/{id}/versions", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_resume_version(
    id: uuid.UUID,
    payload: ResumeVersionCreate,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeVersionResponse:
    """Create a new manual/structured resume version."""
    version = await service.create_version(id, payload, DEFAULT_USER_ID)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return version  # type: ignore[return-value]


@router.get("/{id}/versions/{version_id}", response_model=ResumeVersionResponse)
async def get_resume_version(
    id: uuid.UUID,
    version_id: uuid.UUID,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeVersionResponse:
    """Get detail and extracted text of a specific resume version."""
    version = await service.get_version(id, version_id, DEFAULT_USER_ID)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")
    return version  # type: ignore[return-value]


@router.post("/{id}/versions/{version_id}/clone", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
async def clone_resume_version(
    id: uuid.UUID,
    version_id: uuid.UUID,
    payload: ResumeVersionClone,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeVersionResponse:
    """Clone an immutable version into a new version branch."""
    cloned = await service.clone_version(id, version_id, payload, DEFAULT_USER_ID)
    if not cloned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume or version not found")
    return cloned  # type: ignore[return-value]


@router.post("/{id}/versions/{version_id}/activate", response_model=ResumeResponse)
async def activate_resume_version(
    id: uuid.UUID,
    version_id: uuid.UUID,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeResponse:
    """Designate a version as the active version of the resume."""
    resume = await service.activate_version(id, version_id, DEFAULT_USER_ID)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume or version not found")
    return resume  # type: ignore[return-value]


@router.post("/{id}/versions/upload", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume_version(
    id: uuid.UUID,
    file: UploadFile = File(...),
    version_number: Optional[str] = Form(None),
    change_summary: Optional[str] = Form(None),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeVersionResponse:
    """Upload a PDF or DOCX file, extract text, and append a new immutable version."""
    filename = file.filename or "uploaded_resume.pdf"
    lower_name = filename.lower()
    if not (lower_name.endswith(".pdf") or lower_name.endswith(".docx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only .pdf and .docx files are permitted.",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 10MB limit.")

    try:
        version = await service.upload_and_process_version(
            resume_id=id,
            file_bytes=file_bytes,
            filename=filename,
            user_id=DEFAULT_USER_ID,
            version_number=version_number,
            change_summary=change_summary,
        )
        return version  # type: ignore[return-value]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
