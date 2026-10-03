"""Pydantic schemas for Job Description, Requirements, Analysis, and Matching."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------- Job Description Schemas ----------------
class JobBase(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    source_url: Optional[str] = None
    raw_text: str


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    source_url: Optional[str] = None
    raw_text: Optional[str] = None
    status: Optional[str] = None


# ---------------- Requirement Schemas ----------------
class JobRequirementResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    text: str
    category: str
    importance: str
    extracted_skill: Optional[str] = None
    min_experience_years: Optional[float] = None
    confidence: float
    source_section: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSkillRequirementResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    requirement_id: Optional[uuid.UUID] = None
    skill_name: str
    normalized_skill: str
    category: Optional[str] = None
    importance: str
    min_years: Optional[float] = None
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Analysis Schemas ----------------
class JobAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: str
    summary: Optional[str] = None
    total_requirements: int = 0
    total_skills: int = 0
    raw_analysis_json: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- Match Schemas ----------------
class JobMatchItemResponse(BaseModel):
    id: uuid.UUID
    job_match_id: uuid.UUID
    requirement_id: uuid.UUID
    status: str  # MATCHED, PARTIAL, MISSING, UNKNOWN
    score: float
    matched_entity_type: Optional[str] = None
    matched_entity_id: Optional[str] = None
    matched_entity_name: Optional[str] = None
    evidence_summary: Optional[str] = None
    evidence_source: Optional[str] = None
    explanation: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobMatchWeightsSchema(BaseModel):
    required_skills: float = 0.35
    preferred_skills: float = 0.15
    experience_relevance: float = 0.20
    project_relevance: float = 0.15
    semantic_alignment: float = 0.15


class JobMatchRequest(BaseModel):
    target_type: str = "PROFILE"  # "PROFILE" or "RESUME_VERSION"
    resume_version_id: Optional[uuid.UUID] = None
    weights: Optional[JobMatchWeightsSchema] = None


class JobMatchResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    profile_id: uuid.UUID
    resume_version_id: Optional[uuid.UUID] = None
    target_type: str
    overall_score: float
    breakdown_scores: Dict[str, float]
    score_weights: Dict[str, float]
    status: str
    error_detail: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[JobMatchItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ---------------- Full Job Response ----------------
class JobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    source_url: Optional[str] = None
    raw_text: str
    normalized_text: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    analysis: Optional[JobAnalysisResponse] = None
    requirements: List[JobRequirementResponse] = Field(default_factory=list)
    skills: List[JobSkillRequirementResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

