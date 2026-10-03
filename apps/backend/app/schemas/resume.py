"""Pydantic schemas for Resume and ResumeVersion entities."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------- Resume Version Schemas ----------------
class ResumeVersionBase(BaseModel):
    version_number: str = "v1.0"
    target_job_id: Optional[uuid.UUID] = None
    change_summary: Optional[str] = None


class ResumeVersionCreate(ResumeVersionBase):
    parent_version_id: Optional[uuid.UUID] = None
    extracted_text: Optional[str] = None
    structured_snapshot: Optional[Any] = None


class ResumeVersionClone(BaseModel):
    version_number: str
    change_summary: Optional[str] = None


class ResumeVersionResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    version_number: str
    parent_version_id: Optional[uuid.UUID] = None
    target_job_id: Optional[uuid.UUID] = None
    file_path: Optional[str] = None
    extracted_text: Optional[str] = None
    structured_snapshot: Optional[Any] = None
    change_summary: Optional[str] = None
    status: str
    error_detail: Optional[str] = None
    created_at: datetime
    created_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------- Resume Master Schemas ----------------
class ResumeBase(BaseModel):
    title: str
    description: Optional[str] = None
    target_role: Optional[str] = None
    target_company: Optional[str] = None


class ResumeCreate(ResumeBase):
    initial_version_number: str = "v1.0"


class ResumeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    active_version_id: Optional[uuid.UUID] = None
    status: Optional[str] = None


class ResumeResponse(ResumeBase):
    id: uuid.UUID
    user_id: uuid.UUID
    active_version_id: Optional[uuid.UUID] = None
    status: str
    created_at: datetime
    updated_at: datetime
    versions: List[ResumeVersionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

