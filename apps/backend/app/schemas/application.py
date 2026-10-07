"""Pydantic schemas for Job Applications tracking."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, model_validator


class EmptyStringToNoneModel(BaseModel):
    """Base model that automatically coerces empty strings to None for optional fields."""

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: (None if isinstance(v, str) and v.strip() == "" else v)
                for k, v in data.items()
            }
        return data


class ApplicationBase(EmptyStringToNoneModel):
    company: str
    position: str
    status: str = "APPLIED"
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None
    job_id: Optional[uuid.UUID] = None
    resume_id: Optional[uuid.UUID] = None
    resume_version_id: Optional[uuid.UUID] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(EmptyStringToNoneModel):
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None
    job_id: Optional[uuid.UUID] = None
    resume_id: Optional[uuid.UUID] = None
    resume_version_id: Optional[uuid.UUID] = None


class ApplicationResponse(ApplicationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatsResponse(BaseModel):
    total: int
    applied: int
    screening: int
    interviewing: int
    offered: int
    rejected: int
    withdrawn: int
