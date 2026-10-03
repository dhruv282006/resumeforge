"""Pydantic schemas for Tailoring, Truth Guard, and Version Diffing."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SuggestionEvidenceResponse(BaseModel):
    id: uuid.UUID
    suggestion_id: uuid.UUID
    evidence_type: str
    evidence_id: Optional[uuid.UUID] = None
    source: str
    supporting_text: Optional[str] = None
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeSuggestionResponse(BaseModel):
    id: uuid.UUID
    tailoring_job_id: uuid.UUID
    resume_version_id: uuid.UUID
    section: str
    suggestion_type: str
    original_content: Optional[str] = None
    proposed_content: str
    reason: str
    confidence: float
    status: str
    truth_guard_status: str
    truth_guard_reason: Optional[str] = None
    claim_breakdown_json: Optional[Any] = None
    user_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    evidence_items: List[SuggestionEvidenceResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResumeTailoringJobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_version_id: uuid.UUID
    job_description_id: uuid.UUID
    status: str
    prompt_version: str
    model_metadata: Optional[Dict[str, Any]] = None
    error_detail: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    suggestions: List[ResumeSuggestionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TailorTriggerRequest(BaseModel):
    job_description_id: uuid.UUID
    prompt_override: Optional[str] = None


class SuggestionUpdateRequest(BaseModel):
    status: str = Field(..., description="ACCEPTED, REJECTED, MODIFIED")
    proposed_content: Optional[str] = None
    user_notes: Optional[str] = None


class ApplySuggestionsRequest(BaseModel):
    suggestion_ids: List[uuid.UUID]
    change_summary: Optional[str] = None
    trigger_match: bool = True


class LineDiffItem(BaseModel):
    type: str  # ADD, REMOVE, UNCHANGED
    content: str


class VersionDiffResponse(BaseModel):
    original_version_id: uuid.UUID
    compared_version_id: uuid.UUID
    similarity_ratio: float
    added_lines: int
    removed_lines: int
    unified_diff: str
    line_diffs: List[LineDiffItem]
    section_diffs: Optional[Dict[str, Any]] = None


class TailoringApplyResponse(BaseModel):
    new_version_id: uuid.UUID
    version_number: str
    parent_version_id: uuid.UUID
    accepted_count: int
    diff: VersionDiffResponse
    before_match: Optional[Dict[str, Any]] = None
    after_match: Optional[Dict[str, Any]] = None
    score_delta: Optional[float] = None
    score_improved: bool = True
