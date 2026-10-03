"""Pydantic schemas for Master Career Profile and its sub-entities."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------- Education Schemas ----------------
class EducationBase(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[float] = None
    percentage: Optional[float] = None
    description: Optional[str] = None


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[float] = None
    percentage: Optional[float] = None
    description: Optional[str] = None


class EducationResponse(EducationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Experience Schemas ----------------
class ExperienceBase(BaseModel):
    company: str
    title: str
    employment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    achievements: Optional[List[str]] = Field(default_factory=list)


class ExperienceCreate(ExperienceBase):
    source: str = "USER_PROVIDED"
    confidence: float = 1.0


class ExperienceUpdate(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    achievements: Optional[List[str]] = None


class ExperienceResponse(ExperienceBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    source: str
    confidence: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Skill Schemas ----------------
class SkillBase(BaseModel):
    name: str
    normalized_name: Optional[str] = None
    category: Optional[str] = "TECHNICAL"
    proficiency: Optional[str] = None
    years_of_experience: Optional[float] = None


class SkillCreate(SkillBase):
    source: str = "USER_PROVIDED"
    confidence: float = 1.0


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    normalized_name: Optional[str] = None
    category: Optional[str] = None
    proficiency: Optional[str] = None
    years_of_experience: Optional[float] = None
    source: Optional[str] = None
    confidence: Optional[float] = None


class SkillResponse(SkillBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    source: str
    confidence: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Project Schemas ----------------
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[List[str]] = Field(default_factory=list)
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    project_url: Optional[str] = None
    github_url: Optional[str] = None
    achievements: Optional[List[str]] = Field(default_factory=list)
    metrics: Optional[List[str]] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    project_url: Optional[str] = None
    github_url: Optional[str] = None
    achievements: Optional[List[str]] = None
    metrics: Optional[List[str]] = None


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Certification Schemas ----------------
class CertificationBase(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class CertificationResponse(CertificationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Profile Master Schemas ----------------
class ProfileBase(BaseModel):
    full_name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    preferred_roles: Optional[List[str]] = Field(default_factory=list)
    preferred_industries: Optional[List[str]] = Field(default_factory=list)
    preferred_locations: Optional[List[str]] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    current_status: Optional[str] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    preferred_roles: Optional[List[str]] = None
    preferred_industries: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    years_of_experience: Optional[float] = None
    current_status: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    educations: List[EducationResponse] = Field(default_factory=list)
    experiences: List[ExperienceResponse] = Field(default_factory=list)
    skills: List[SkillResponse] = Field(default_factory=list)
    projects: List[ProjectResponse] = Field(default_factory=list)
    certifications: List[CertificationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProfileCompletenessResponse(BaseModel):
    overall: int
    sections: dict[str, int]

