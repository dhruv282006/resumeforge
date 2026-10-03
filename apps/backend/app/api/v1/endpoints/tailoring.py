"""API Endpoints for Resume Tailoring, Truth Guard, and Version Diffing."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.profile import Profile
from app.models.resume_version import ResumeVersion
from app.models.tailoring import (
    ResumeSuggestion,
    ResumeTailoringJob,
    SuggestionEvidence,
)
from app.schemas.job import JobMatchRequest
from app.schemas.tailoring import (
    ApplySuggestionsRequest,
    ResumeSuggestionResponse,
    ResumeTailoringJobResponse,
    SuggestionUpdateRequest,
    TailorTriggerRequest,
    TailoringApplyResponse,
    VersionDiffResponse,
)
from app.services.diff_service import diff_service
from app.services.job_service import JobService
from app.services.resume_service import DEFAULT_USER_ID, ResumeService
from app.services.tailoring import resume_tailoring_service
from app.services.truth_guard import truth_guard_service

router = APIRouter()


@router.post("/{version_id}/tailor", response_model=ResumeTailoringJobResponse, status_code=status.HTTP_201_CREATED)
async def trigger_resume_tailoring(
    version_id: uuid.UUID,
    payload: TailorTriggerRequest,
    db: AsyncSession = Depends(get_db),
) -> ResumeTailoringJobResponse:
    """Generate grounded, section-level tailoring suggestions verified by Truth Guard."""
    # 1. Fetch ResumeVersion
    stmt_rv = select(ResumeVersion).where(ResumeVersion.id == version_id)
    res_rv = await db.execute(stmt_rv)
    rv = res_rv.scalar_one_or_none()
    if not rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")

    # 2. Fetch JobDescription with requirements & skills
    stmt_jd = (
        select(JobDescription)
        .options(
            selectinload(JobDescription.requirements),
            selectinload(JobDescription.skills),
            selectinload(JobDescription.analysis),
        )
        .where(JobDescription.id == payload.job_description_id)
    )
    res_jd = await db.execute(stmt_jd)
    jd = res_jd.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    # 3. Fetch Candidate Profile with all evidence
    stmt_prof = (
        select(Profile)
        .options(
            selectinload(Profile.skills),
            selectinload(Profile.experiences),
            selectinload(Profile.projects),
            selectinload(Profile.educations),
            selectinload(Profile.certifications),
        )
        .where(Profile.user_id == DEFAULT_USER_ID)
    )
    res_prof = await db.execute(stmt_prof)
    prof = res_prof.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    # 4. Generate tailoring job and execute Truth Guard
    job = await resume_tailoring_service.create_tailoring_job(
        db=db,
        user_id=DEFAULT_USER_ID,
        resume_version=rv,
        job_description=jd,
        profile=prof,
    )

    # 5. Eager-load suggestions and evidence for response
    stmt_job_full = (
        select(ResumeTailoringJob)
        .options(
            selectinload(ResumeTailoringJob.suggestions).selectinload(ResumeSuggestion.evidence_items)
        )
        .where(ResumeTailoringJob.id == job.id)
    )
    res_full = await db.execute(stmt_job_full)
    job_full = res_full.scalar_one()

    return job_full  # type: ignore[return-value]


@router.get("/tailoring-jobs/{job_id}", response_model=ResumeTailoringJobResponse)
@router.get("/{version_id}/tailoring-jobs/{job_id}", response_model=ResumeTailoringJobResponse)
async def get_tailoring_job(
    job_id: uuid.UUID,
    version_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> ResumeTailoringJobResponse:
    """Retrieve full details of a tailoring job including suggestions, claims, and evidence."""
    stmt = (
        select(ResumeTailoringJob)
        .options(
            selectinload(ResumeTailoringJob.suggestions).selectinload(ResumeSuggestion.evidence_items)
        )
        .where(ResumeTailoringJob.id == job_id)
    )
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tailoring job not found")
    return job  # type: ignore[return-value]


@router.get("/{version_id}/tailoring-jobs", response_model=List[ResumeTailoringJobResponse])
async def list_version_tailoring_jobs(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[ResumeTailoringJobResponse]:
    """List all tailoring runs performed for a specific resume version."""
    stmt = (
        select(ResumeTailoringJob)
        .options(
            selectinload(ResumeTailoringJob.suggestions).selectinload(ResumeSuggestion.evidence_items)
        )
        .where(ResumeTailoringJob.resume_version_id == version_id)
        .order_by(ResumeTailoringJob.created_at.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())  # type: ignore[return-value]


@router.patch("/suggestions/{suggestion_id}", response_model=ResumeSuggestionResponse)
async def update_suggestion(
    suggestion_id: uuid.UUID,
    payload: SuggestionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ResumeSuggestionResponse:
    """Review, accept, reject, or edit a tailoring suggestion with re-verification."""
    stmt = (
        select(ResumeSuggestion)
        .options(
            selectinload(ResumeSuggestion.evidence_items),
            selectinload(ResumeSuggestion.resume_version),
        )
        .where(ResumeSuggestion.id == suggestion_id)
    )
    res = await db.execute(stmt)
    sug = res.scalar_one_or_none()
    if not sug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

    sug.status = payload.status
    if payload.user_notes is not None:
        sug.user_notes = payload.user_notes

    # If user edited proposed content, run Truth Guard verification on their edit
    if payload.proposed_content and payload.proposed_content != sug.proposed_content:
        sug.proposed_content = payload.proposed_content

        # Fetch profile
        stmt_prof = (
            select(Profile)
            .options(
                selectinload(Profile.skills),
                selectinload(Profile.experiences),
                selectinload(Profile.projects),
                selectinload(Profile.educations),
                selectinload(Profile.certifications),
            )
            .where(Profile.user_id == DEFAULT_USER_ID)
        )
        res_prof = await db.execute(stmt_prof)
        prof = res_prof.scalar_one_or_none()

        kb = truth_guard_service.build_candidate_knowledge_base(
            profile=prof,
            resume_version=sug.resume_version,
        )
        evaluation = truth_guard_service.validate_suggestion(
            section=sug.section,
            suggestion_type=sug.suggestion_type,
            original_content=sug.original_content,
            proposed_content=sug.proposed_content,
            knowledge_base=kb,
        )

        sug.truth_guard_status = evaluation.status
        sug.truth_guard_reason = evaluation.reason
        sug.confidence = evaluation.overall_confidence
        sug.claim_breakdown_json = [
            {
                "claim_text": c.claim_text,
                "status": c.status,
                "reasons": c.reasons,
                "detected_metrics": c.detected_metrics,
                "unsupported_metrics": c.unsupported_metrics,
                "detected_skills": c.detected_skills,
                "unsupported_skills": c.unsupported_skills,
            }
            for c in evaluation.claims
        ]

    await db.commit()
    await db.refresh(sug)
    return sug  # type: ignore[return-value]


@router.post("/{version_id}/apply-suggestions", response_model=TailoringApplyResponse, status_code=status.HTTP_201_CREATED)
async def apply_suggestions(
    version_id: uuid.UUID,
    payload: ApplySuggestionsRequest,
    db: AsyncSession = Depends(get_db),
) -> TailoringApplyResponse:
    """Create new immutable ResumeVersion applying accepted suggestions, compute diff and re-score."""
    # 1. Fetch parent ResumeVersion
    stmt_rv = select(ResumeVersion).where(ResumeVersion.id == version_id)
    res_rv = await db.execute(stmt_rv)
    parent_rv = res_rv.scalar_one_or_none()
    if not parent_rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent resume version not found")

    # 2. Fetch accepted suggestions
    stmt_sug = (
        select(ResumeSuggestion)
        .where(
            ResumeSuggestion.id.in_(payload.suggestion_ids),
            ResumeSuggestion.resume_version_id == version_id,
        )
    )
    res_sug = await db.execute(stmt_sug)
    suggestions = list(res_sug.scalars().all())

    if not suggestions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No matching suggestions found to apply")

    # Mark them ACCEPTED
    for s in suggestions:
        s.status = "ACCEPTED"

    # 3. Apply suggestions onto structured snapshot
    base_snapshot = parent_rv.structured_snapshot or {}
    updated_snapshot = diff_service.apply_accepted_suggestions(base_snapshot, suggestions)
    updated_text = diff_service.render_snapshot_to_text(updated_snapshot)

    # 4. Compute next version number (e.g. 1.0 -> 1.1)
    parent_vnum = parent_rv.version_number
    try:
        if "." in parent_vnum:
            parts = parent_vnum.lstrip("v").split(".")
            next_minor = int(parts[-1]) + 1
            new_vnum = f"v{parts[0]}.{next_minor}"
        else:
            new_vnum = f"{parent_vnum}.1"
    except Exception:
        new_vnum = f"{parent_vnum}-tailored"

    # 5. Create new immutable ResumeVersion
    new_version = ResumeVersion(
        resume_id=parent_rv.resume_id,
        version_number=new_vnum,
        parent_version_id=parent_rv.id,
        target_job_id=parent_rv.target_job_id,
        extracted_text=updated_text,
        structured_snapshot=updated_snapshot,
        change_summary=payload.change_summary or f"Applied {len(suggestions)} tailored suggestions from version {parent_vnum}",
        status="READY",
        created_by=DEFAULT_USER_ID,
    )
    db.add(new_version)
    await db.commit()
    await db.refresh(new_version)

    # 6. Compute diff between parent and new version
    orig_text = parent_rv.extracted_text or diff_service.render_snapshot_to_text(base_snapshot)
    text_diff = diff_service.compute_text_diff(orig_text, updated_text)
    section_diffs = diff_service.compute_snapshot_diff(base_snapshot, updated_snapshot)

    diff_response = VersionDiffResponse(
        original_version_id=parent_rv.id,
        compared_version_id=new_version.id,
        similarity_ratio=text_diff["similarity_ratio"],
        added_lines=text_diff["added_lines"],
        removed_lines=text_diff["removed_lines"],
        unified_diff=text_diff["unified_diff"],
        line_diffs=text_diff["line_diffs"],
        section_diffs=section_diffs,
    )

    # 7. Before / After Match Re-scoring
    before_match_data: Optional[Dict[str, Any]] = None
    after_match_data: Optional[Dict[str, Any]] = None
    score_delta: Optional[float] = None
    score_improved = True

    target_job_id = parent_rv.target_job_id
    if payload.trigger_match and target_job_id:
        job_service = JobService(db)

        # Before match lookup
        stmt_bm = (
            select(JobMatch)
            .where(
                JobMatch.job_description_id == target_job_id,
                JobMatch.resume_version_id == parent_rv.id,
            )
            .order_by(JobMatch.created_at.desc())
        )
        res_bm = await db.execute(stmt_bm)
        before_match = res_bm.scalars().first()
        if before_match:
            before_match_data = {
                "overall_score": before_match.overall_score,
                "required_skills_score": before_match.required_skills_score,
                "preferred_skills_score": before_match.preferred_skills_score,
                "experience_score": before_match.experience_score,
                "project_score": before_match.project_score,
                "semantic_score": before_match.semantic_score,
                "matched_count": before_match.matched_count,
                "missing_count": before_match.missing_count,
            }

        # Run after match
        after_match = await job_service.match_job(
            job_id=target_job_id,
            payload=JobMatchRequest(
                target_type="RESUME_VERSION",
                resume_version_id=new_version.id,
            ),
            user_id=DEFAULT_USER_ID,
        )

        if after_match:
            after_match_data = {
                "overall_score": after_match.overall_score,
                "required_skills_score": after_match.required_skills_score,
                "preferred_skills_score": after_match.preferred_skills_score,
                "experience_score": after_match.experience_score,
                "project_score": after_match.project_score,
                "semantic_score": after_match.semantic_score,
                "matched_count": after_match.matched_count,
                "missing_count": after_match.missing_count,
            }

            if before_match:
                score_delta = round(after_match.overall_score - before_match.overall_score, 2)
                score_improved = score_delta >= 0

    return TailoringApplyResponse(
        new_version_id=new_version.id,
        version_number=new_version.version_number,
        parent_version_id=parent_rv.id,
        accepted_count=len(suggestions),
        diff=diff_response,
        before_match=before_match_data,
        after_match=after_match_data,
        score_delta=score_delta,
        score_improved=score_improved,
    )


@router.get("/{version_id}/diff/{compare_version_id}", response_model=VersionDiffResponse)
async def get_version_diff(
    version_id: uuid.UUID,
    compare_version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> VersionDiffResponse:
    """Compare two resume versions and return line-by-line diff and section metrics."""
    stmt_v1 = select(ResumeVersion).where(ResumeVersion.id == version_id)
    stmt_v2 = select(ResumeVersion).where(ResumeVersion.id == compare_version_id)

    res1 = await db.execute(stmt_v1)
    res2 = await db.execute(stmt_v2)

    v1 = res1.scalar_one_or_none()
    v2 = res2.scalar_one_or_none()

    if not v1 or not v2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both resume versions not found")

    text1 = v1.extracted_text or diff_service.render_snapshot_to_text(v1.structured_snapshot or {})
    text2 = v2.extracted_text or diff_service.render_snapshot_to_text(v2.structured_snapshot or {})

    text_diff = diff_service.compute_text_diff(text1, text2)
    section_diffs = diff_service.compute_snapshot_diff(v1.structured_snapshot, v2.structured_snapshot)

    return VersionDiffResponse(
        original_version_id=v1.id,
        compared_version_id=v2.id,
        similarity_ratio=text_diff["similarity_ratio"],
        added_lines=text_diff["added_lines"],
        removed_lines=text_diff["removed_lines"],
        unified_diff=text_diff["unified_diff"],
        line_diffs=text_diff["line_diffs"],
        section_diffs=section_diffs,
    )
