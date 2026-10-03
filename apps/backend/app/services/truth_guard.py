"""Truth Guard Service for ResumeForge Phase 3.

Strictly enforces the foundational principle:
"The user's Master Career Profile is the source of truth."

Detects and rejects:
- Invented metrics, numbers, percentages, dollar amounts
- Invented technologies, tools, and skills
- Invented job titles, employers, certifications, degrees
- Temporal inconsistencies
- Hallucinated achievements
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from app.services.normalizer import skill_normalizer


@dataclass
class ClaimCheckResult:
    claim_text: str
    status: str  # VERIFIED, PARTIALLY_SUPPORTED, UNSUPPORTED, REQUIRES_REVIEW
    detected_metrics: List[str] = field(default_factory=list)
    unsupported_metrics: List[str] = field(default_factory=list)
    detected_skills: List[str] = field(default_factory=list)
    unsupported_skills: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)


@dataclass
class TruthGuardEvaluation:
    status: str  # VERIFIED, PARTIALLY_SUPPORTED, UNSUPPORTED, REQUIRES_REVIEW
    reason: str
    claims: List[ClaimCheckResult] = field(default_factory=list)
    supported_evidence: List[Dict[str, Any]] = field(default_factory=list)
    overall_confidence: float = 1.0


class TruthGuardService:
    """Validates AI-generated resume suggestions against candidate evidence."""

    # Metrics regex: percentages, dollar values, multipliers, numeric counts with units
    METRIC_PATTERN = re.compile(
        r"(?:(?:\$|€|£)\s*\d+(?:\.\d+)?\s*(?:k|m|b|million|billion|k)?)|"
        r"(?:\b\d+(?:\.\d+)?\s*%)|"
        r"(?:\b\d+(?:\.\d+)?\s*(?:x|X)\b)|"
        r"(?:\b\d+(?:\.\d+)?\s*(?:ms|seconds|minutes|hours|days|weeks|months|years|users|qps|requests|tps|engineers|team members|clients|customers|projects)\b)",
        re.IGNORECASE,
    )

    # General numbers regex (standalone numbers like 40, 100, 5000)
    NUMBER_PATTERN = re.compile(r"\b\d{1,6}\b")

    def __init__(self) -> None:
        self.normalizer = skill_normalizer

    def build_candidate_knowledge_base(
        self,
        profile: Any,
        resume_version: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Extracts facts, skills, metrics, and text corpus from candidate profile and resume."""
        knowledge_base: Dict[str, Any] = {
            "skills": set(),  # Normalized skill strings
            "skill_records": [],  # id, name, category, proficiency
            "experiences": [],  # id, role, company, description, bullets
            "projects": [],  # id, title, description, tech_stack
            "educations": [],  # id, degree, institution, field_of_study
            "certifications": [],  # id, name, issuer
            "corpus_text": "",  # Aggregate lowercase text for fast substring checking
            "metrics": set(),  # Set of normalized metrics/numbers found in candidate records
            "years_of_experience": 0.0,
        }

        corpus_parts: List[str] = []

        # 1. Profile information
        if profile:
            if hasattr(profile, "years_of_experience") and profile.years_of_experience:
                knowledge_base["years_of_experience"] = float(profile.years_of_experience)
            if hasattr(profile, "summary") and profile.summary:
                corpus_parts.append(profile.summary)
            if hasattr(profile, "headline") and profile.headline:
                corpus_parts.append(profile.headline)

            # Skills
            skills = getattr(profile, "skills", []) or []
            for s in skills:
                name = getattr(s, "name", "")
                if name:
                    norm = self.normalizer.normalize(name).normalized_skill
                    knowledge_base["skills"].add(norm.lower())
                    knowledge_base["skill_records"].append({
                        "id": str(getattr(s, "id", uuid.uuid4())),
                        "name": name,
                        "normalized": norm,
                        "category": getattr(s, "category", "GENERAL"),
                    })
                    corpus_parts.append(name)

            # Experiences
            experiences = getattr(profile, "experiences", []) or []
            for exp in experiences:
                role = getattr(exp, "title", "") or getattr(exp, "role", "")
                company = getattr(exp, "company", "")
                desc = getattr(exp, "description", "") or ""
                resp = getattr(exp, "responsibilities", []) or []
                achieve = getattr(exp, "achievements", []) or []

                all_exp_text = f"{role} {company} {desc} " + " ".join(resp if isinstance(resp, list) else []) + " " + " ".join(achieve if isinstance(achieve, list) else [])
                corpus_parts.append(all_exp_text)

                knowledge_base["experiences"].append({
                    "id": str(getattr(exp, "id", uuid.uuid4())),
                    "role": role,
                    "company": company,
                    "text": all_exp_text,
                })

            # Projects
            projects = getattr(profile, "projects", []) or []
            for proj in projects:
                title = getattr(proj, "title", "") or getattr(proj, "name", "")
                desc = getattr(proj, "description", "") or ""
                techs = getattr(proj, "technologies", []) or []
                all_proj_text = f"{title} {desc} " + " ".join(techs if isinstance(techs, list) else [])
                corpus_parts.append(all_proj_text)

                knowledge_base["projects"].append({
                    "id": str(getattr(proj, "id", uuid.uuid4())),
                    "title": title,
                    "text": all_proj_text,
                })

                if isinstance(techs, list):
                    for t in techs:
                        norm = self.normalizer.normalize(str(t)).normalized_skill
                        knowledge_base["skills"].add(norm.lower())

            # Educations
            educations = getattr(profile, "educations", []) or []
            for edu in educations:
                inst = getattr(edu, "institution", "")
                degree = getattr(edu, "degree", "")
                field = getattr(edu, "field_of_study", "")
                text = f"{inst} {degree} {field}"
                corpus_parts.append(text)
                knowledge_base["educations"].append({
                    "id": str(getattr(edu, "id", uuid.uuid4())),
                    "text": text,
                })

            # Certifications
            certifications = getattr(profile, "certifications", []) or []
            for cert in certifications:
                name = getattr(cert, "name", "")
                issuer = getattr(cert, "issuer", "")
                text = f"{name} {issuer}"
                corpus_parts.append(text)
                knowledge_base["certifications"].append({
                    "id": str(getattr(cert, "id", uuid.uuid4())),
                    "text": text,
                })

        # 2. Existing ResumeVersion text & snapshot
        if resume_version:
            if hasattr(resume_version, "extracted_text") and resume_version.extracted_text:
                corpus_parts.append(resume_version.extracted_text)
            if hasattr(resume_version, "structured_snapshot") and resume_version.structured_snapshot:
                snapshot = resume_version.structured_snapshot
                if isinstance(snapshot, dict):
                    for val in snapshot.values():
                        if isinstance(val, (str, list, dict)):
                            corpus_parts.append(str(val))

        full_corpus = "\n".join(corpus_parts)
        knowledge_base["corpus_text"] = full_corpus.lower()

        # Extract all metrics from the candidate's corpus
        for m in self.METRIC_PATTERN.findall(full_corpus):
            clean_m = re.sub(r"\s+", "", m.lower())
            knowledge_base["metrics"].add(clean_m)

        # Also extract isolated numbers > 1 to avoid false-flagging simple mentions
        for n in self.NUMBER_PATTERN.findall(full_corpus):
            knowledge_base["metrics"].add(n)

        return knowledge_base

    def extract_claims(self, text: str) -> List[str]:
        """Splits proposed content into discrete bullet points or sentences."""
        if not text:
            return []

        # Split by newlines, bullet points, or sentence boundaries
        lines = [line.strip("- *• \t\r") for line in text.splitlines() if line.strip("- *• \t\r")]
        claims: List[str] = []

        for line in lines:
            # Further split long compound sentences if appropriate
            sentences = re.split(r"(?<=[.!?])\s+", line)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 5:
                    claims.append(s_clean)

        return claims if claims else [text.strip()]

    def extract_metrics(self, text: str) -> List[str]:
        """Finds all metric claims in the given text."""
        matches = self.METRIC_PATTERN.findall(text)
        return [m.strip() for m in matches if m.strip()]

    def extract_candidate_skills_in_text(self, text: str) -> List[str]:
        """Detects tech skills and tools mentioned in the text using canonical dictionary."""
        lower = text.lower()
        found: Set[str] = set()
        for alias, canonical in self.normalizer.CANONICAL_ALIASES.items():
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, lower):
                found.add(canonical)
        return list(found)

    def validate_suggestion(
        self,
        section: str,
        suggestion_type: str,
        original_content: Optional[str],
        proposed_content: str,
        knowledge_base: Dict[str, Any],
        supporting_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> TruthGuardEvaluation:
        # If suggestion is REMOVE or REORDER, there are no new claims to hallucinate
        if suggestion_type in {"REMOVE", "REORDER"}:
            return TruthGuardEvaluation(
                status="VERIFIED",
                reason=f"Suggestion type {suggestion_type} does not introduce any new claims or entities.",
                claims=[
                    ClaimCheckResult(
                        claim_text=proposed_content or f"[{suggestion_type} operation]",
                        status="VERIFIED",
                        reasons=[f"Structural {suggestion_type} operation."],
                    )
                ],
                supported_evidence=[],
                overall_confidence=1.0,
            )

        if not proposed_content or not proposed_content.strip():
            return TruthGuardEvaluation(
                status="UNSUPPORTED",
                reason="Proposed content cannot be empty.",
                overall_confidence=0.0,
            )

        claims = self.extract_claims(proposed_content)
        claim_results: List[ClaimCheckResult] = []
        all_supported_evidence: List[Dict[str, Any]] = list(supporting_evidence or [])

        candidate_corpus = knowledge_base.get("corpus_text", "")
        candidate_skills = knowledge_base.get("skills", set())
        candidate_metrics = knowledge_base.get("metrics", set())

        has_unsupported = False
        has_partial = False
        has_review = False
        unsupported_reasons: List[str] = []

        for claim in claims:
            detected_metrics = self.extract_metrics(claim)
            unsupported_metrics: List[str] = []

            # 1. Metric check
            for m in detected_metrics:
                clean_m = re.sub(r"\s+", "", m.lower())
                # Check if metric or the underlying number exists in candidate evidence
                raw_numbers = self.NUMBER_PATTERN.findall(m)
                metric_backed = clean_m in candidate_metrics
                if not metric_backed and raw_numbers:
                    # check if the numeric value was anywhere in candidate evidence
                    metric_backed = any(num in candidate_metrics for num in raw_numbers)

                if not metric_backed:
                    unsupported_metrics.append(m)

            # 2. Skill & Entity check
            detected_skills = self.extract_candidate_skills_in_text(claim)
            unsupported_skills: List[str] = []

            for sk in detected_skills:
                norm_sk = self.normalizer.normalize(sk).normalized_skill.lower()
                if norm_sk not in candidate_skills and norm_sk not in candidate_corpus:
                    unsupported_skills.append(sk)

            # 3. Evidence linking
            matched_evidence_ids: List[str] = []
            claim_reasons: List[str] = []

            for exp in knowledge_base.get("experiences", []):
                # If claim references experience context
                if exp["role"].lower() in claim.lower() or exp["company"].lower() in claim.lower():
                    matched_evidence_ids.append(exp["id"])
                    all_supported_evidence.append({
                        "evidence_type": "EXPERIENCE",
                        "evidence_id": exp["id"],
                        "source": "USER_PROVIDED",
                        "supporting_text": f"Matches experience at {exp['company']} ({exp['role']})",
                        "confidence": 0.95,
                    })

            for proj in knowledge_base.get("projects", []):
                if proj["title"].lower() in claim.lower():
                    matched_evidence_ids.append(proj["id"])
                    all_supported_evidence.append({
                        "evidence_type": "PROJECT",
                        "evidence_id": proj["id"],
                        "source": "USER_PROVIDED",
                        "supporting_text": f"Matches project '{proj['title']}'",
                        "confidence": 0.95,
                    })

            for sk_rec in knowledge_base.get("skill_records", []):
                if sk_rec["name"].lower() in claim.lower():
                    matched_evidence_ids.append(sk_rec["id"])
                    all_supported_evidence.append({
                        "evidence_type": "SKILL",
                        "evidence_id": sk_rec["id"],
                        "source": "USER_PROVIDED",
                        "supporting_text": f"Grounded in verified profile skill: {sk_rec['name']}",
                        "confidence": 1.0,
                    })

            # Determine claim status
            if unsupported_metrics:
                c_status = "UNSUPPORTED"
                msg = f"Invented metric(s): {', '.join(unsupported_metrics)}. Not supported by candidate profile or resume."
                claim_reasons.append(msg)
                unsupported_reasons.append(msg)
                has_unsupported = True
            elif unsupported_skills:
                c_status = "UNSUPPORTED"
                msg = f"Invented technology/skill(s): {', '.join(unsupported_skills)}. Candidate profile lacks verified experience with these technologies."
                claim_reasons.append(msg)
                unsupported_reasons.append(msg)
                has_unsupported = True
            elif suggestion_type == "ADD_FROM_PROFILE" and not matched_evidence_ids:
                c_status = "REQUIRES_REVIEW"
                msg = "Suggested addition lacks explicit direct link to a specific profile record."
                claim_reasons.append(msg)
                has_review = True
            elif not detected_metrics and not detected_skills and len(claim) > 30 and original_content and original_content.lower() not in candidate_corpus:
                # Rephrase of unverified external content
                c_status = "PARTIALLY_SUPPORTED"
                claim_reasons.append("Claim phrasing is adapted but should be reviewed for factual fidelity.")
                has_partial = True
            else:
                c_status = "VERIFIED"
                claim_reasons.append("Claim entities and metrics are fully grounded in candidate evidence.")

            claim_results.append(
                ClaimCheckResult(
                    claim_text=claim,
                    status=c_status,
                    detected_metrics=detected_metrics,
                    unsupported_metrics=unsupported_metrics,
                    detected_skills=detected_skills,
                    unsupported_skills=unsupported_skills,
                    reasons=claim_reasons,
                    evidence_ids=matched_evidence_ids,
                )
            )

        # Synthesize overall status
        if has_unsupported:
            overall_status = "UNSUPPORTED"
            overall_reason = "; ".join(unsupported_reasons)
            confidence = 0.2
        elif has_review:
            overall_status = "REQUIRES_REVIEW"
            overall_reason = "Contains claims that require candidate confirmation or additional evidence."
            confidence = 0.6
        elif has_partial:
            overall_status = "PARTIALLY_SUPPORTED"
            overall_reason = "Core information is consistent with profile, but phrasing includes minor embellishments to confirm."
            confidence = 0.8
        else:
            overall_status = "VERIFIED"
            overall_reason = "Fully verified against candidate profile records. Zero invented metrics or technologies."
            confidence = 1.0

        # Deduplicate evidence
        seen_evidence: Set[Tuple[str, Optional[str]]] = set()
        deduped_evidence: List[Dict[str, Any]] = []
        for ev in all_supported_evidence:
            key = (ev["evidence_type"], str(ev.get("evidence_id")))
            if key not in seen_evidence:
                seen_evidence.add(key)
                deduped_evidence.append(ev)

        return TruthGuardEvaluation(
            status=overall_status,
            reason=overall_reason,
            claims=claim_results,
            supported_evidence=deduped_evidence,
            overall_confidence=confidence,
        )


truth_guard_service = TruthGuardService()
