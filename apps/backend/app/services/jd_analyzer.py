"""Job Description analysis pipeline.

Combines rule-based / deterministic extraction, regex section detection,
canonical skill normalization, and optional structured LLM extraction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.providers.base import LLMProvider, get_llm_provider
from app.core.config import get_settings
from app.models.job_description import JobAnalysis, JobDescription
from app.models.job_requirement import JobRequirement, JobSkillRequirement
from app.services.normalizer import skill_normalizer

logger = structlog.get_logger(__name__)


# ---------------- Pydantic Schemas for LLM Output ----------------
class LLMRequirementItem(BaseModel):
    text: str
    category: str = "OTHER"  # SKILL, EXPERIENCE, EDUCATION, RESPONSIBILITY, CERTIFICATION, DOMAIN_KNOWLEDGE, OTHER
    importance: str = "REQUIRED"  # REQUIRED, PREFERRED, OPTIONAL, UNKNOWN
    extracted_skill: Optional[str] = None
    min_experience_years: Optional[float] = None
    confidence: float = 0.9


class LLMJDParsingResult(BaseModel):
    summary: str = ""
    requirements: List[LLMRequirementItem] = Field(default_factory=list)


# ---------------- Deterministic Extractor ----------------
class DeterministicJDExtractor:
    """Rule-based extractor for job descriptions."""

    SECTION_PATTERNS = [
        ("PREFERRED", re.compile(r"^(?:preferred|bonus|nice to have|plus|additional)\b.*:?", re.IGNORECASE)),
        ("REQUIRED", re.compile(r"^(?:requirements|qualifications|minimum qualifications|basic qualifications|must have|what you bring|what we need)\b.*:?", re.IGNORECASE)),
        ("RESPONSIBILITIES", re.compile(r"^(?:responsibilities|duties|what you will do|what you'll do|the role|key responsibilities)\b.*:?", re.IGNORECASE)),
    ]

    YEARS_EXP_REGEX = re.compile(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:to\s*\d+\+?)?\s*years?\b",
        re.IGNORECASE,
    )

    DEGREE_REGEX = re.compile(
        r"\b(bachelor(?:'s)?|master(?:'s)?|ph\.?d\.?|b\.?s\.?|m\.?s\.?|degree in (?:computer science|engineering|software|data science|math|related field))\b",
        re.IGNORECASE,
    )

    BULLET_REGEX = re.compile(r"^[\s•*·\-–—▪▫➢✓]+\s*")

    def normalize_text(self, text: str) -> str:
        """Clean raw JD text: normalize line endings and whitespace."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace non-standard bullets with hyphens
        text = re.sub(r"^[•*·–—▪▫➢✓]\s*", "- ", text, flags=re.MULTILINE)
        return text.strip()

    def parse_sections_and_items(self, text: str) -> List[Dict[str, Any]]:
        """Split text into lines, detect section headings, and extract candidate items."""
        normalized = self.normalize_text(text)
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]

        current_section = "GENERAL"
        current_importance = "UNKNOWN"
        items: List[Dict[str, Any]] = []

        for line in lines:
            # Check if this line is a section heading
            heading_matched = False
            for sec_name, pattern in self.SECTION_PATTERNS:
                if pattern.search(line) and len(line) < 60:
                    current_section = sec_name
                    if sec_name == "REQUIRED":
                        current_importance = "REQUIRED"
                    elif sec_name == "PREFERRED":
                        current_importance = "PREFERRED"
                    elif sec_name == "RESPONSIBILITIES":
                        current_importance = "REQUIRED"
                    heading_matched = True
                    break

            if heading_matched:
                continue

            clean_line = self.BULLET_REGEX.sub("", line).strip()
            if len(clean_line) < 8:
                continue

            # Classify item
            category, skill, min_years = self._classify_line(clean_line)
            importance = current_importance

            # Refine importance if line mentions "preferred" or "nice to have"
            lower_line = clean_line.lower()
            if "preferred" in lower_line or "nice to have" in lower_line or "plus" in lower_line:
                importance = "PREFERRED"
            elif "must have" in lower_line or "required" in lower_line:
                importance = "REQUIRED"

            items.append({
                "text": clean_line,
                "category": category,
                "importance": importance,
                "extracted_skill": skill,
                "min_experience_years": min_years,
                "confidence": 0.85,
                "source_section": current_section,
            })

        return items

    def _classify_line(self, line: str) -> Tuple[str, Optional[str], Optional[float]]:
        """Classify line category, detect skills, and extract years of experience."""
        min_years: Optional[float] = None
        years_match = self.YEARS_EXP_REGEX.search(line)
        if years_match:
            try:
                min_years = float(years_match.group(1))
            except ValueError:
                pass

        # Check degree
        if self.DEGREE_REGEX.search(line):
            return "EDUCATION", None, min_years

        # Check certification
        if re.search(r"\b(certified|certification|license|pmp|cissp|aws certified)\b", line, re.IGNORECASE):
            return "CERTIFICATION", None, min_years

        # Look for known canonical skills in line
        lower_line = line.lower()
        words = re.findall(r"\b[A-Za-z0-9#\+\.]+\b", line)
        detected_skill = None
        for w in words:
            norm = skill_normalizer.normalize(w)
            if norm.normalization_source == "ALIAS_MAP":
                detected_skill = norm.normalized_skill
                break

        # If min_years present, it is an EXPERIENCE requirement (e.g. 5+ years of ...)
        if min_years is not None:
            return "EXPERIENCE", detected_skill, min_years

        if detected_skill:
            return "SKILL", detected_skill, None

        if re.search(r"\b(knowledge of|grasp of|proficiency (?:in|with)|familiarity with|expertise in|experience with|skilled in|fluency in)\b", line, re.IGNORECASE):
            return "SKILL", None, None

        if re.search(r"^(?:build|develop|lead|design|maintain|collaborate|architect|implement|write|test)\b", line, re.IGNORECASE):
            return "RESPONSIBILITY", None, None

        return "OTHER", None, min_years


# ---------------- Main Job Description Analysis Service ----------------
class JobDescriptionAnalyzer:
    """Orchestrates job description normalization, extraction, and persistence."""

    def __init__(
        self,
        session: AsyncSession,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        self.session = session
        self.extractor = DeterministicJDExtractor()
        self.llm = llm_provider

    async def analyze_job(self, job: JobDescription) -> JobAnalysis:
        """Run analysis on JobDescription and persist requirements and skills."""
        # Ensure relationships are loaded in async context
        stmt = (
            select(JobDescription)
            .where(JobDescription.id == job.id)
            .options(
                selectinload(JobDescription.requirements),
                selectinload(JobDescription.skills),
                selectinload(JobDescription.analysis),
            )
        )
        res = await self.session.execute(stmt)
        loaded_job = res.scalars().first()
        if loaded_job:
            job = loaded_job

        normalized_text = self.extractor.normalize_text(job.raw_text)
        job.normalized_text = normalized_text

        # 1. Deterministic Rule-Based Extraction (Always available)
        rule_items = self.extractor.parse_sections_and_items(job.raw_text)

        # 2. Optional LLM Structured Extraction
        llm_items: List[LLMRequirementItem] = []
        llm_summary = ""
        llm_succeeded = False

        if self.llm is None:
            try:
                settings = get_settings()
                self.llm = get_llm_provider(settings)
            except Exception as exc:
                logger.info("No LLM provider configured", error=str(exc))

        if self.llm:
            try:
                prompt = (
                    "Extract structured requirements from this job description.\n"
                    "Identify requirements, categories (SKILL, EXPERIENCE, EDUCATION, RESPONSIBILITY, CERTIFICATION, DOMAIN_KNOWLEDGE, OTHER), "
                    "importance (REQUIRED, PREFERRED, OPTIONAL), and any specific skill name and minimum years of experience.\n\n"
                    f"Job Description:\n{job.raw_text[:4000]}"
                )
                system_prompt = (
                    "You are a technical recruiting parser. Return ONLY valid JSON adhering to schema."
                )
                res = await self.llm.extract_structured(
                    prompt=prompt,
                    schema=LLMJDParsingResult,
                    system_prompt=system_prompt,
                )
                if res and res.requirements:
                    llm_items = res.requirements
                    llm_summary = res.summary
                    llm_succeeded = True
            except Exception as exc:
                logger.warning("LLM JD extraction unavailable or failed; using deterministic extractor", error=str(exc))
                llm_succeeded = False

        # 3. Merge or fallback
        final_requirements: List[Dict[str, Any]] = []
        if llm_succeeded and llm_items:
            for item in llm_items:
                final_requirements.append({
                    "text": item.text,
                    "category": item.category.upper(),
                    "importance": item.importance.upper(),
                    "extracted_skill": item.extracted_skill,
                    "min_experience_years": item.min_experience_years,
                    "confidence": float(item.confidence),
                    "source_section": "LLM_PARSED",
                })
        else:
            final_requirements = rule_items

        # Ensure at least minimal requirements exist
        if not final_requirements:
            final_requirements = [{
                "text": line,
                "category": "OTHER",
                "importance": "REQUIRED",
                "extracted_skill": None,
                "min_experience_years": None,
                "confidence": 0.7,
                "source_section": "RAW",
            } for line in normalized_text.split("\n")[:10] if len(line) > 15]

        # 4. Clear old requirements/skills if re-analyzing
        job.requirements.clear()
        job.skills.clear()

        # 5. Populate JobRequirement and JobSkillRequirement records
        created_skills_count = 0
        seen_normalized_skills = set()

        for req_dict in final_requirements:
            req = JobRequirement(
                job_id=job.id,
                text=req_dict["text"],
                category=req_dict.get("category", "OTHER"),
                importance=req_dict.get("importance", "REQUIRED"),
                extracted_skill=req_dict.get("extracted_skill"),
                min_experience_years=req_dict.get("min_experience_years"),
                confidence=req_dict.get("confidence", 0.9),
                source_section=req_dict.get("source_section", "GENERAL"),
            )
            job.requirements.append(req)

            # If requirement references a skill or is of category SKILL
            skill_candidate = req_dict.get("extracted_skill")
            if not skill_candidate and req_dict.get("category") == "SKILL":
                skill_candidate = req_dict["text"]

            if skill_candidate:
                norm = skill_normalizer.normalize(skill_candidate)
                if norm.normalized_skill and norm.normalized_skill.lower() not in seen_normalized_skills:
                    seen_normalized_skills.add(norm.normalized_skill.lower())
                    skill_req = JobSkillRequirement(
                        job_id=job.id,
                        requirement=req,
                        skill_name=norm.original_skill,
                        normalized_skill=norm.normalized_skill,
                        category="TECHNICAL",
                        importance=req.importance,
                        min_years=req.min_experience_years,
                        confidence=req.confidence,
                    )
                    job.skills.append(skill_req)
                    created_skills_count += 1

        # 6. Create / Update JobAnalysis record
        status = "COMPLETED" if (llm_succeeded or rule_items) else "AI_PROCESSING_UNAVAILABLE"
        summary = llm_summary or f"Extracted {len(job.requirements)} requirements and {created_skills_count} skills."

        if job.analysis:
            analysis = job.analysis
            analysis.status = status
            analysis.summary = summary
            analysis.total_requirements = len(job.requirements)
            analysis.total_skills = created_skills_count
            analysis.raw_analysis_json = {
                "source": "LLM" if llm_succeeded else "DETERMINISTIC",
                "total_requirements": len(job.requirements),
                "total_skills": created_skills_count,
            }
        else:
            analysis = JobAnalysis(
                job_id=job.id,
                status=status,
                summary=summary,
                total_requirements=len(job.requirements),
                total_skills=created_skills_count,
                raw_analysis_json={
                    "source": "LLM" if llm_succeeded else "DETERMINISTIC",
                    "total_requirements": len(job.requirements),
                    "total_skills": created_skills_count,
                },
            )
            job.analysis = analysis
            self.session.add(analysis)

        job.status = "PARSED"
        await self.session.commit()
        return analysis
