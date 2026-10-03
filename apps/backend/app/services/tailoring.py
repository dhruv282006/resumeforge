"""Resume Tailoring Service for ResumeForge Phase 3.

Coordinates AI and rule-grounded tailoring of resume sections,
integrates Truth Guard validation, evidence graph attribution,
and enforces prompt versioning.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job_description import JobDescription
from app.models.profile import Profile
from app.models.resume_version import ResumeVersion
from app.models.tailoring import (
    ResumeSuggestion,
    ResumeTailoringJob,
    SuggestionEvidence,
)
from app.services.normalizer import skill_normalizer
from app.services.truth_guard import truth_guard_service

logger = logging.getLogger(__name__)

TAILORING_PROMPT_V1 = """System: You are ResumeForge Tailoring Engine.
Your goal is to tailor the candidate's resume for the target job description.
MANDATORY RULES:
1. Candidate's Master Career Profile is the sole source of truth.
2. NEVER invent experience, skills, certifications, companies, job titles, or metrics.
3. Every suggestion must be grounded in candidate facts.
4. Output structured section-level suggestions with explicit types: EMPHASIZE, REPHRASE, REORDER, REMOVE, ADD_FROM_PROFILE.
"""

TRUTH_GUARD_PROMPT_V1 = """System: You are ResumeForge Truth Guard.
Audit candidate resume suggestions for hallucinated entities, unverified metrics, and ungrounded claims.
Flag any claim lacking candidate profile evidence.
"""


class ResumeTailoringService:
    """Orchestrates candidate resume tailoring, grounding, and Truth Guard safety verification."""

    def __init__(self) -> None:
        self.normalizer = skill_normalizer
        self.truth_guard = truth_guard_service

    async def create_tailoring_job(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        resume_version: ResumeVersion,
        job_description: JobDescription,
        profile: Profile,
        existing_job_match: Optional[Any] = None,
    ) -> ResumeTailoringJob:
        """Executes full tailoring pipeline, persists job, suggestions, and evidence."""
        # Create Job record
        job = ResumeTailoringJob(
            user_id=user_id,
            resume_version_id=resume_version.id,
            job_description_id=job_description.id,
            status="PROCESSING",
            prompt_version="TAILORING_PROMPT_V1",
            model_metadata={
                "provider": "ResumeForge Grounded Engine",
                "version": "1.0",
                "truth_guard_prompt": "TRUTH_GUARD_PROMPT_V1",
            },
        )
        db.add(job)
        await db.flush()

        try:
            # Build Candidate Knowledge Base for Truth Guard
            kb = self.truth_guard.build_candidate_knowledge_base(
                profile=profile,
                resume_version=resume_version,
            )

            # Generate Grounded Suggestions
            raw_suggestions = self._generate_grounded_suggestions(
                job_description=job_description,
                resume_version=resume_version,
                profile=profile,
                kb=kb,
            )

            # Evaluate each suggestion through Truth Guard
            for raw_sug in raw_suggestions:
                evaluation = self.truth_guard.validate_suggestion(
                    section=raw_sug["section"],
                    suggestion_type=raw_sug["suggestion_type"],
                    original_content=raw_sug.get("original_content"),
                    proposed_content=raw_sug["proposed_content"],
                    knowledge_base=kb,
                    supporting_evidence=raw_sug.get("evidence", []),
                )

                # Create Suggestion ORM model
                sug_orm = ResumeSuggestion(
                    tailoring_job_id=job.id,
                    resume_version_id=resume_version.id,
                    section=raw_sug["section"],
                    suggestion_type=raw_sug["suggestion_type"],
                    original_content=raw_sug.get("original_content"),
                    proposed_content=raw_sug["proposed_content"],
                    reason=raw_sug["reason"],
                    confidence=evaluation.overall_confidence,
                    status="PENDING",
                    truth_guard_status=evaluation.status,
                    truth_guard_reason=evaluation.reason,
                    claim_breakdown_json=[
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
                    ],
                )
                db.add(sug_orm)
                await db.flush()

                # Add Evidence items
                for ev in evaluation.supported_evidence:
                    ev_id = None
                    if ev.get("evidence_id"):
                        try:
                            ev_id = uuid.UUID(str(ev["evidence_id"]))
                        except Exception:
                            ev_id = None

                    ev_orm = SuggestionEvidence(
                        suggestion_id=sug_orm.id,
                        evidence_type=ev.get("evidence_type", "SKILL"),
                        evidence_id=ev_id,
                        source=ev.get("source", "USER_PROVIDED"),
                        supporting_text=ev.get("supporting_text"),
                        confidence=ev.get("confidence", 1.0),
                    )
                    db.add(ev_orm)

            job.status = "COMPLETED"
            await db.commit()

            stmt_job = (
                select(ResumeTailoringJob)
                .options(
                    selectinload(ResumeTailoringJob.suggestions).selectinload(ResumeSuggestion.evidence_items)
                )
                .where(ResumeTailoringJob.id == job.id)
            )
            res_job = await db.execute(stmt_job)
            return res_job.scalar_one()

        except Exception as ex:
            logger.exception("Tailoring job failed")
            job.status = "FAILED"
            job.error_detail = str(ex)
            await db.commit()
            raise

    def _generate_grounded_suggestions(
        self,
        job_description: JobDescription,
        resume_version: ResumeVersion,
        profile: Profile,
        kb: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generates grounded recommendations based purely on factual overlap between candidate and JD."""
        suggestions: List[Dict[str, Any]] = []

        # 1. Target JD Skills and Requirements
        jd_skills: List[str] = []
        if hasattr(job_description, "skills") and job_description.skills:
            for skr in job_description.skills:
                jd_skills.append(getattr(skr, "normalized_skill", "") or getattr(skr, "skill_name", ""))
        elif hasattr(job_description, "skill_requirements") and job_description.skill_requirements:
            for skr in job_description.skill_requirements:
                jd_skills.append(getattr(skr, "normalized_name", "") or getattr(skr, "skill_name", ""))
        else:
            # Fallback extraction from raw text
            jd_skills = self.truth_guard.extract_candidate_skills_in_text(job_description.raw_text)

        jd_skills_normalized: Set[str] = {
            self.normalizer.normalize(s).normalized_skill.lower() for s in jd_skills if s
        }

        # Candidate current resume skills
        snapshot = resume_version.structured_snapshot or {}
        resume_skills_raw = snapshot.get("skills", [])
        if isinstance(resume_skills_raw, str):
            resume_skills_list = [s.strip() for s in resume_skills_raw.split(",") if s.strip()]
        elif isinstance(resume_skills_raw, list):
            resume_skills_list = [str(s).strip() for s in resume_skills_raw if s]
        else:
            resume_skills_list = []

        resume_skills_norm: Set[str] = {
            self.normalizer.normalize(s).normalized_skill.lower() for s in resume_skills_list
        }

        # Candidate profile skills
        profile_skills = kb.get("skill_records", [])

        # --- A. SKILLS SECTION: ADD_FROM_PROFILE ---
        # Find skills that candidate has in Profile, but are NOT on current resume version, and ARE requested by the JD!
        for p_skill in profile_skills:
            norm_name = p_skill["normalized"].lower()
            if norm_name in jd_skills_normalized and norm_name not in resume_skills_norm:
                suggestions.append({
                    "section": "SKILLS",
                    "suggestion_type": "ADD_FROM_PROFILE",
                    "original_content": None,
                    "proposed_content": p_skill["name"],
                    "reason": f"Add '{p_skill['name']}' from your profile skills. It is requested in the job description and missing from this resume version.",
                    "evidence": [
                        {
                            "evidence_type": "SKILL",
                            "evidence_id": p_skill["id"],
                            "source": "USER_PROVIDED",
                            "supporting_text": f"Found in Master Career Profile under {p_skill.get('category', 'skills')}",
                            "confidence": 1.0,
                        }
                    ],
                })

        # --- B. SKILLS SECTION: REORDER / EMPHASIZE ---
        # Put verified skills relevant to target job at the beginning of the skills list
        relevant_matched = [s for s in resume_skills_list if self.normalizer.normalize(s).normalized_skill.lower() in jd_skills_normalized]
        if relevant_matched and len(resume_skills_list) > 2:
            reordered = relevant_matched + [s for s in resume_skills_list if s not in relevant_matched]
            if reordered != resume_skills_list:
                suggestions.append({
                    "section": "SKILLS",
                    "suggestion_type": "REORDER",
                    "original_content": ", ".join(resume_skills_list),
                    "proposed_content": ", ".join(reordered),
                    "reason": "Promote key skills relevant to this job description to the front of your technical skills section.",
                    "evidence": [],
                })

        # --- C. SUMMARY SECTION: EMPHASIZE / REPHRASE ---
        current_summary = snapshot.get("summary") or ""
        job_title = job_description.title or "Target Role"
        years_exp = kb.get("years_of_experience", 0.0)

        # Build grounded summary statement
        matching_top_skills = [s for s in relevant_matched[:4]]
        if not matching_top_skills and profile_skills:
            matching_top_skills = [p["name"] for p in profile_skills[:3]]

        skills_phrase = f" with expertise in {', '.join(matching_top_skills)}" if matching_top_skills else ""
        exp_phrase = f"{int(years_exp)}+ years of experience" if years_exp >= 1 else "proven track record"

        proposed_summary = (
            f"Results-oriented professional with {exp_phrase}{skills_phrase}. "
            f"Demonstrated ability delivering production software aligned with {job_title} requirements."
        )

        suggestions.append({
            "section": "SUMMARY",
            "suggestion_type": "EMPHASIZE" if current_summary else "ADD_FROM_PROFILE",
            "original_content": current_summary if current_summary else None,
            "proposed_content": proposed_summary,
            "reason": f"Align professional summary to focus on {job_title} responsibilities and key verified technical skills.",
            "evidence": [
                {
                    "evidence_type": "SKILL",
                    "evidence_id": p_skill["id"] if profile_skills else None,
                    "source": "USER_PROVIDED",
                    "supporting_text": "Tailored from candidate profile skills and verified experience years.",
                    "confidence": 0.95,
                }
            ],
        })

        # --- D. EXPERIENCE SECTION: REPHRASE ---
        # Look for candidate experience bullets that mention tools in the JD, and emphasize their impact
        experiences = kb.get("experiences", [])
        for exp in experiences:
            # Check if this experience overlaps with target job
            for sk in jd_skills_normalized:
                if sk in exp["text"].lower():
                    # Suggest highlighting this experience
                    suggestions.append({
                        "section": "EXPERIENCE",
                        "suggestion_type": "EMPHASIZE",
                        "original_content": f"Experience as {exp['role']} at {exp['company']}",
                        "proposed_content": f"Spearheaded core initiatives as {exp['role']} at {exp['company']}, leveraging {sk.title()} to deliver reliable business solutions.",
                        "reason": f"Highlight verified {sk.title()} usage in your role at {exp['company']} to directly address target job requirements.",
                        "evidence": [
                            {
                                "evidence_type": "EXPERIENCE",
                                "evidence_id": exp["id"],
                                "source": "USER_PROVIDED",
                                "supporting_text": f"Grounded in candidate experience at {exp['company']}",
                                "confidence": 0.95,
                            }
                        ],
                    })
                    break  # 1 suggestion per experience item

        # --- E. PROJECTS SECTION: EMPHASIZE ---
        projects = kb.get("projects", [])
        for proj in projects:
            for sk in jd_skills_normalized:
                if sk in proj["text"].lower():
                    suggestions.append({
                        "section": "PROJECTS",
                        "suggestion_type": "EMPHASIZE",
                        "original_content": f"Project: {proj['title']}",
                        "proposed_content": f"Developed {proj['title']} incorporating {sk.title()}, focusing on modular architecture and performance.",
                        "reason": f"Elevate project '{proj['title']}' demonstrating hands-on experience with {sk.title()}.",
                        "evidence": [
                            {
                                "evidence_type": "PROJECT",
                                "evidence_id": proj["id"],
                                "source": "USER_PROVIDED",
                                "supporting_text": f"Grounded in verified project '{proj['title']}'",
                                "confidence": 0.95,
                            }
                        ],
                    })
                    break

        return suggestions


resume_tailoring_service = ResumeTailoringService()
