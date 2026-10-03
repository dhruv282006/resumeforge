"""Hybrid Job Matching Engine with transparent scoring and evidence attribution."""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job_description import JobDescription
from app.models.job_match import JobMatch, JobMatchItem
from app.models.job_requirement import JobRequirement
from app.models.profile import Profile
from app.models.resume_version import ResumeVersion
from app.services.embedding import (
    EmbeddingService,
    cosine_similarity,
    get_embedding_provider,
)
from app.services.normalizer import skill_normalizer

logger = structlog.get_logger(__name__)


@dataclass
class MatchingWeights:
    """Weights for the 5 components of the Job Match Score (sum to 1.0)."""
    required_skills: float = 0.35
    preferred_skills: float = 0.15
    experience_relevance: float = 0.20
    project_relevance: float = 0.15
    semantic_alignment: float = 0.15

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class MatchingConfig:
    """Configuration for thresholds and evidence matching."""
    match_threshold: float = 0.78
    partial_threshold: float = 0.58
    weights: MatchingWeights = field(default_factory=MatchingWeights)


@dataclass
class EvidenceItem:
    """A granular piece of candidate evidence extracted from profile or resume."""
    entity_type: str  # SKILL, EXPERIENCE, PROJECT, EDUCATION, CERTIFICATION, RESUME_TEXT
    entity_id: str
    entity_name: str
    text_content: str
    source: str = "USER_PROVIDED"  # USER_PROVIDED, RESUME_PARSED, AI_INFERRED, IMPORTED
    normalized_names: List[str] = field(default_factory=list)


class CandidateEvidenceExtractor:
    """Extracts structured evidence items from Master Profile or Resume Version."""

    def extract_evidence(
        self,
        profile: Profile,
        resume_version: Optional[ResumeVersion] = None,
    ) -> List[EvidenceItem]:
        evidence: List[EvidenceItem] = []

        # 1. Skills
        for sk in profile.skills:
            norm = skill_normalizer.normalize(sk.name)
            evidence.append(
                EvidenceItem(
                    entity_type="SKILL",
                    entity_id=str(sk.id),
                    entity_name=sk.name,
                    text_content=f"Skill: {sk.name} ({sk.proficiency or 'proficient'})",
                    source=sk.source or "USER_PROVIDED",
                    normalized_names=[norm.normalized_skill.lower(), sk.name.lower()],
                )
            )

        # 2. Experiences
        for exp in profile.experiences:
            ach_text = " ".join(exp.achievements or [])
            full_text = f"{exp.title} at {exp.company}. {exp.description or ''} {ach_text}"
            words = re.findall(r"\b[A-Za-z0-9#\+\.]+\b", full_text)
            normalized_skills = [skill_normalizer.normalize(w).normalized_skill.lower() for w in words]
            evidence.append(
                EvidenceItem(
                    entity_type="EXPERIENCE",
                    entity_id=str(exp.id),
                    entity_name=f"{exp.title} at {exp.company}",
                    text_content=full_text.strip(),
                    source=exp.source or "USER_PROVIDED",
                    normalized_names=list(set(normalized_skills)),
                )
            )

        # 3. Projects
        for proj in profile.projects:
            tech_list = proj.technologies or []
            ach_text = " ".join(proj.achievements or [])
            full_text = f"Project {proj.name} ({proj.role or 'Contributor'}): {proj.description or ''}. Built with: {', '.join(tech_list)}. {ach_text}"
            norm_techs = [skill_normalizer.normalize(t).normalized_skill.lower() for t in tech_list]
            evidence.append(
                EvidenceItem(
                    entity_type="PROJECT",
                    entity_id=str(proj.id),
                    entity_name=proj.name,
                    text_content=full_text.strip(),
                    source="USER_PROVIDED",
                    normalized_names=list(set(norm_techs)),
                )
            )

        # 4. Educations
        for edu in profile.educations:
            full_text = f"{edu.degree or 'Degree'} in {edu.field_of_study or 'Field'} from {edu.institution}. {edu.description or ''}"
            evidence.append(
                EvidenceItem(
                    entity_type="EDUCATION",
                    entity_id=str(edu.id),
                    entity_name=f"{edu.degree or 'Degree'} at {edu.institution}",
                    text_content=full_text.strip(),
                    source="USER_PROVIDED",
                )
            )

        # 5. Certifications
        for cert in profile.certifications:
            full_text = f"Certification {cert.name} issued by {cert.issuing_organization or 'Unknown Organization'}"
            evidence.append(
                EvidenceItem(
                    entity_type="CERTIFICATION",
                    entity_id=str(cert.id),
                    entity_name=cert.name,
                    text_content=full_text.strip(),
                    source="USER_PROVIDED",
                )
            )

        # 6. Resume Version Text (if provided)
        if resume_version and resume_version.extracted_text:
            chunks = [
                chunk.strip()
                for chunk in resume_version.extracted_text.split("\n\n")
                if len(chunk.strip()) > 30
            ]
            for idx, chunk in enumerate(chunks[:15]):
                words = re.findall(r"\b[A-Za-z0-9#\+\.]+\b", chunk)
                norm_words = [skill_normalizer.normalize(w).normalized_skill.lower() for w in words]
                evidence.append(
                    EvidenceItem(
                        entity_type="RESUME_TEXT",
                        entity_id=f"resume_chunk_{idx}",
                        entity_name=f"Resume Snippet #{idx + 1}",
                        text_content=chunk,
                        source="RESUME_PARSED",
                        normalized_names=list(set(norm_words)),
                    )
                )

        return evidence


class MatchingEngine:
    """Computes transparent, evidence-grounded Job Match Score and individual requirement matches."""

    def __init__(
        self,
        session: AsyncSession,
        config: Optional[MatchingConfig] = None,
    ) -> None:
        self.session = session
        self.config = config or MatchingConfig()
        self.evidence_extractor = CandidateEvidenceExtractor()
        self.embedding_service = EmbeddingService(session)

    async def compute_match(
        self,
        job: JobDescription,
        profile: Profile,
        resume_version: Optional[ResumeVersion] = None,
        custom_weights: Optional[MatchingWeights] = None,
    ) -> JobMatch:
        """Execute hybrid matching between JobDescription and candidate profile/resume."""
        # Ensure profile relationships are eager loaded in async context
        stmt_p = (
            select(Profile)
            .where(Profile.id == profile.id)
            .options(
                selectinload(Profile.skills),
                selectinload(Profile.experiences),
                selectinload(Profile.projects),
                selectinload(Profile.educations),
                selectinload(Profile.certifications),
            )
        )
        res_p = await self.session.execute(stmt_p)
        loaded_p = res_p.scalars().first()
        if loaded_p:
            profile = loaded_p

        # Ensure job requirements are eager loaded in async context
        stmt_j = (
            select(JobDescription)
            .where(JobDescription.id == job.id)
            .options(
                selectinload(JobDescription.requirements),
                selectinload(JobDescription.skills),
            )
        )
        res_j = await self.session.execute(stmt_j)
        loaded_j = res_j.scalars().first()
        if loaded_j:
            job = loaded_j

        weights = custom_weights or self.config.weights
        evidence_list = self.evidence_extractor.extract_evidence(profile, resume_version)

        # 1. Compute/retrieve embeddings for all candidate evidence chunks
        evidence_vectors: List[Tuple[EvidenceItem, List[float]]] = []
        for ev in evidence_list:
            vec = await self.embedding_service.get_or_create_embedding(
                source_type=f"CANDIDATE_{ev.entity_type}",
                source_id=ev.entity_id,
                text=ev.text_content,
            )
            evidence_vectors.append((ev, vec))

        # Collect verified skills for MISSING vs UNKNOWN differentiation
        candidate_skills_set = {
            s.normalized_skill.lower()
            for s in [skill_normalizer.normalize(sk.name) for sk in profile.skills]
            if s.normalized_skill
        }
        for ev in evidence_list:
            candidate_skills_set.update(ev.normalized_names)

        # Collect all canonical skills requested across the job description
        job_skills_set = {
            s.normalized_skill.lower()
            for s in job.skills
            if s.normalized_skill
        }
        for req in job.requirements:
            req_words = re.findall(r"\b[A-Za-z0-9#\+\.]+\b", req.text)
            for rw in req_words:
                norm_rw = skill_normalizer.normalize(rw)
                if norm_rw.normalization_source == "ALIAS_MAP" and norm_rw.normalized_skill:
                    job_skills_set.add(norm_rw.normalized_skill.lower())

        match_items: List[JobMatchItem] = []

        # Scoring accumulators
        req_skills_scores: List[float] = []
        pref_skills_scores: List[float] = []
        exp_scores: List[float] = []
        proj_scores: List[float] = []
        semantic_sims: List[float] = []

        # 2. Match each requirement against evidence
        for req in job.requirements:
            req_vec = await self.embedding_service.get_or_create_embedding(
                source_type="JOB_REQUIREMENT",
                source_id=str(req.id),
                text=req.text,
            )

            best_ev: Optional[EvidenceItem] = None
            best_sim = 0.0
            is_lexical_exact = False

            # Extract any canonical skills mentioned in req.text
            req_words = re.findall(r"\b[A-Za-z0-9#\+\.]+\b", req.text)
            line_skills: List[str] = []
            for rw in req_words:
                norm_rw = skill_normalizer.normalize(rw)
                if norm_rw.normalization_source == "ALIAS_MAP" and norm_rw.normalized_skill:
                    line_skills.append(norm_rw.normalized_skill.lower())
            if req.extracted_skill:
                norm_ext = skill_normalizer.normalize(req.extracted_skill).normalized_skill
                if norm_ext:
                    line_skills.append(norm_ext.lower())
            line_skills = list(set(line_skills))

            # Check if any or all line_skills are present in candidate skills / evidence
            matched_skills = [s for s in line_skills if s in candidate_skills_set]

            if line_skills:
                if matched_skills:
                    is_lexical_exact = True
                    best_sim = 1.0 if len(matched_skills) == len(line_skills) else 0.90
                    for ev, vec in evidence_vectors:
                        if any(ms in ev.normalized_names for ms in matched_skills):
                            best_ev = ev
                            break
            elif req.extracted_skill:
                norm_target_skill = skill_normalizer.normalize(req.extracted_skill).normalized_skill
                if norm_target_skill:
                    for ev, vec in evidence_vectors:
                        if norm_target_skill.lower() in ev.normalized_names:
                            is_lexical_exact = True
                            best_ev = ev
                            best_sim = 1.0
                            break

            # If not exact lexical match, search semantically across all evidence
            if not is_lexical_exact:
                for ev, vec in evidence_vectors:
                    sim = cosine_similarity(req_vec, vec)
                    if sim > best_sim:
                        best_sim = sim
                        best_ev = ev

            # Special grounded evaluation for EXPERIENCE requirements
            cand_years = profile.years_of_experience or 0.0
            req_years = req.min_experience_years
            exp_evs = [ev for ev, _ in evidence_vectors if ev.entity_type == "EXPERIENCE"]

            status: str
            confidence_score: float
            explanation: str

            if req.category == "EXPERIENCE" or req_years is not None:
                if exp_evs and (req_years is None or cand_years >= req_years):
                    status = "MATCHED"
                    confidence_score = 0.95
                    best_ev = exp_evs[0]
                    target_yr_str = f"required {req_years:.1f} years" if req_years else "experience criteria"
                    explanation = f"Candidate has {cand_years:.1f} years of verified experience (meets {target_yr_str}) at {best_ev.entity_name}."
                elif req_years is not None and cand_years < req_years:
                    status = "PARTIAL" if cand_years > 0 else "MISSING"
                    confidence_score = round(min(1.0, cand_years / max(1.0, req_years)), 2)
                    best_ev = exp_evs[0] if exp_evs else None
                    explanation = f"Candidate has {cand_years:.1f} years of experience, below the required {req_years:.1f} years."
                elif is_lexical_exact or best_sim >= self.config.match_threshold:
                    status = "MATCHED"
                    confidence_score = max(best_sim, 0.90)
                    explanation = f"Matched requirement with verified candidate evidence from {best_ev.entity_name}."
                else:
                    status = "MISSING"
                    confidence_score = best_sim
                    explanation = "No matching candidate experience found for this requirement."
            elif is_lexical_exact or best_sim >= self.config.match_threshold:
                status = "MATCHED"
                confidence_score = max(best_sim, 0.90 if is_lexical_exact else best_sim)
                explanation = f"Matched requirement with verified candidate evidence from {best_ev.entity_name}."
            elif best_sim >= self.config.partial_threshold:
                status = "PARTIAL"
                confidence_score = best_sim
                explanation = f"Partially matches concepts found in candidate {best_ev.entity_name}."
            else:
                confidence_score = best_sim
                if line_skills and not matched_skills:
                    status = "MISSING"
                    explanation = f"Required skill ({', '.join(line_skills)}) is absent from candidate profile and evidence."
                elif req.category == "SKILL":
                    if len(profile.skills) >= 3:
                        status = "MISSING"
                        explanation = "Requirement skill is absent from candidate's verified skills and project records."
                    else:
                        status = "UNKNOWN"
                        explanation = "Candidate profile does not contain enough data to verify this requirement."
                elif req.category in {"RESPONSIBILITY", "DOMAIN_KNOWLEDGE", "OTHER"}:
                    status = "UNKNOWN"
                    explanation = "Unable to determine candidate alignment from available profile evidence."
                else:
                    status = "MISSING"
                    explanation = "No matching candidate evidence found for this requirement."

            semantic_sims.append(best_sim)

            # Route scores to breakdown components
            num_score = 1.0 if status == "MATCHED" else (0.5 if status == "PARTIAL" else 0.0)
            if req.category == "SKILL" or line_skills:
                if req.importance == "PREFERRED":
                    pref_skills_scores.append(num_score)
                else:
                    req_skills_scores.append(num_score)
            elif req.category == "EXPERIENCE":
                exp_scores.append(num_score)
            elif req.importance == "PREFERRED":
                pref_skills_scores.append(num_score)
            elif req.importance == "REQUIRED":
                req_skills_scores.append(num_score)

            if best_ev and best_ev.entity_type == "EXPERIENCE" and req.category != "EXPERIENCE":
                exp_scores.append(num_score)

            if best_ev and best_ev.entity_type == "PROJECT":
                proj_scores.append(num_score)

            # Build JobMatchItem
            item = JobMatchItem(
                requirement_id=req.id,
                status=status,
                score=round(confidence_score, 2),
                matched_entity_type=best_ev.entity_type if (status in {"MATCHED", "PARTIAL"} and best_ev) else None,
                matched_entity_id=best_ev.entity_id if (status in {"MATCHED", "PARTIAL"} and best_ev) else None,
                matched_entity_name=best_ev.entity_name if (status in {"MATCHED", "PARTIAL"} and best_ev) else None,
                evidence_summary=best_ev.text_content[:300] if (status in {"MATCHED", "PARTIAL"} and best_ev) else None,
                evidence_source=best_ev.source if (status in {"MATCHED", "PARTIAL"} and best_ev) else "NONE",
                explanation=explanation,
            )
            match_items.append(item)

        # 4. Calculate Component Breakdown (0 to 100)
        def _calc_pct(scores: List[float], default: float = 0.0) -> float:
            if not scores:
                return default
            return round(float(sum(scores) / len(scores)) * 100.0, 1)

        # Ground experience and project relevance
        proj_evs = [ev for ev, _ in evidence_vectors if ev.entity_type == "PROJECT"]
        if proj_evs:
            proj_scores_list = []
            for ev in proj_evs:
                overlap = [s for s in ev.normalized_names if s in job_skills_set]
                proj_scores_list.append(1.0 if overlap else 0.2)
            proj_relevance_val = round(float(sum(proj_scores_list) / len(proj_scores_list)) * 100.0, 1)
        else:
            proj_relevance_val = 0.0

        if exp_evs:
            exp_scores_list = []
            cand_years = profile.years_of_experience or 0.0
            for ev in exp_evs:
                overlap = [s for s in ev.normalized_names if s in job_skills_set]
                exp_scores_list.append(1.0 if overlap else 0.3)
            duration_factor = 1.0 if (cand_years >= 3.0 or any(
                req.min_experience_years and cand_years >= req.min_experience_years
                for req in job.requirements
            )) else 0.5
            exp_relevance_val = round(float(sum(exp_scores_list) / len(exp_scores_list)) * duration_factor * 100.0, 1)
        else:
            exp_relevance_val = 0.0

        breakdown = {
            "required_skills": _calc_pct(req_skills_scores, default=0.0),
            "preferred_skills": _calc_pct(pref_skills_scores, default=0.0),
            "experience_relevance": exp_relevance_val,
            "project_relevance": proj_relevance_val,
            "semantic_alignment": _calc_pct(semantic_sims, default=0.0),
        }

        # 5. Calculate Weighted Job Match Score
        overall_score = round(
            breakdown["required_skills"] * weights.required_skills
            + breakdown["preferred_skills"] * weights.preferred_skills
            + breakdown["experience_relevance"] * weights.experience_relevance
            + breakdown["project_relevance"] * weights.project_relevance
            + breakdown["semantic_alignment"] * weights.semantic_alignment,
            1,
        )
        overall_score = max(0.0, min(100.0, overall_score))

        # 6. Build and persist JobMatch record
        job_match = JobMatch(
            job_id=job.id,
            user_id=profile.user_id,
            profile_id=profile.id,
            resume_version_id=resume_version.id if resume_version else None,
            target_type="RESUME_VERSION" if resume_version else "PROFILE",
            overall_score=overall_score,
            breakdown_scores=breakdown,
            score_weights=weights.to_dict(),
            status="COMPLETED",
            items=match_items,
        )
        self.session.add(job_match)
        job.status = "MATCHED"
        await self.session.commit()
        return job_match
