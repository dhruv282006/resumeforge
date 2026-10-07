"""Standalone End-to-End Synthetic Candidate Workflow Verification for ResumeForge.

Connects to the real local PostgreSQL database (with pgvector) and real Gemini API provider.
Executes the full candidate lifecycle:
  1. Create User & Profile
  2. Add candidate master career data (Education, Skills, Experience, Projects)
  3. Create Resume Version 1.0
  4. Add target Job Description
  5. Extract Job Intelligence (via JDAnalyzer + Gemini)
  6. Calculate Job Match score & gap analysis for Version 1.0
  7. Generate Tailoring Suggestions (via ResumeTailoringService)
  8. Truth Guard Verification (Grounded vs Hallucinated claims)
  9. Apply Accepted Suggestions -> Create Resume Version 1.1 (lineage verified)
  10. Generate Unified & Snapshot Diff
  11. Recalculate Job Match -> Before/After comparison & score improvement
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from typing import Any, Dict, List

# Ensure apps/backend is on python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine
from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.job_description import JobAnalysis, JobDescription
from app.models.job_match import JobMatch
from app.models.job_requirement import JobRequirement, JobSkillRequirement
from app.models.profile import Profile
from app.models.project import Project
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.skill import Skill
from app.models.tailoring import ResumeSuggestion, ResumeTailoringJob
from app.models.user import User
from app.schemas.job import JobMatchRequest
from app.services.diff_service import diff_service
from app.services.jd_analyzer import JobDescriptionAnalyzer
from app.services.job_service import JobService
from app.services.tailoring import resume_tailoring_service
from app.services.truth_guard import truth_guard_service

TEST_USER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")


async def run_e2e_workflow() -> bool:
    settings = get_settings()
    print("=" * 80)
    print("RESUMEFORGE END-TO-END WORKFLOW INTEGRATION VERIFICATION")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"Database: PostgreSQL (asyncpg)")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # Cleanup any previous run data for test user
        print("\n[Step 0] Cleaning up any previous test artifacts for test user...")
        # Delete test matches, jobs, resumes, profile
        stmt_del_jobs = select(JobDescription).where(JobDescription.user_id == TEST_USER_ID)
        res_jobs = await db.execute(stmt_del_jobs)
        for j in res_jobs.scalars().all():
            await db.delete(j)

        stmt_del_res = select(Resume).where(Resume.user_id == TEST_USER_ID)
        res_res = await db.execute(stmt_del_res)
        for r in res_res.scalars().all():
            await db.delete(r)

        stmt_del_prof = select(Profile).where(Profile.user_id == TEST_USER_ID)
        res_prof = await db.execute(stmt_del_prof)
        for p in res_prof.scalars().all():
            await db.delete(p)

        stmt_del_u = select(User).where(User.id == TEST_USER_ID)
        res_u = await db.execute(stmt_del_u)
        for u in res_u.scalars().all():
            await db.delete(u)

        await db.commit()
        print("  Cleanup complete.")

        # ----------------------------------------------------------------------
        # 1. Create User & Profile
        # ----------------------------------------------------------------------
        print("\n[Step 1] Creating User & Master Career Profile...")
        user = User(
            id=TEST_USER_ID,
            email="marcus.vance@resumeforge.internal",
            full_name="Marcus Vance",
        )
        db.add(user)

        profile = Profile(
            user_id=TEST_USER_ID,
            full_name="Marcus Vance",
            headline="Lead Cloud & Backend Engineer | Python, Distributed Systems & AI",
            summary=(
                "Experienced Backend and Cloud Engineer with 7+ years architecting scalable "
                "microservices, event-driven data pipelines, and AI-enabled platforms using Python, "
                "FastAPI, PostgreSQL, Redis, Docker, and Kubernetes. Proven track record reducing "
                "latency and leading distributed engineering teams."
            ),
            years_of_experience=7.5,
            location="San Francisco, CA",
        )
        db.add(profile)
        await db.flush()
        print(f"  User ID: {user.id}")
        print(f"  Profile ID: {profile.id} ({profile.full_name} - {profile.headline})")

        # ----------------------------------------------------------------------
        # 2. Add Candidate Master Career Data
        # ----------------------------------------------------------------------
        print("\n[Step 2] Adding Candidate Master Career Data (Skills, Experience, Education, Projects)...")
        skills = [
            Skill(profile_id=profile.id, name="Python", category="LANGUAGES", proficiency="EXPERT"),
            Skill(profile_id=profile.id, name="FastAPI", category="FRAMEWORKS", proficiency="EXPERT"),
            Skill(profile_id=profile.id, name="PostgreSQL", category="DATABASES", proficiency="EXPERT"),
            Skill(profile_id=profile.id, name="Redis", category="DATABASES", proficiency="ADVANCED"),
            Skill(profile_id=profile.id, name="Docker", category="DEVOPS", proficiency="EXPERT"),
            Skill(profile_id=profile.id, name="Kubernetes", category="DEVOPS", proficiency="ADVANCED"),
            Skill(profile_id=profile.id, name="AWS", category="CLOUD", proficiency="ADVANCED"),
            Skill(profile_id=profile.id, name="TypeScript", category="LANGUAGES", proficiency="INTERMEDIATE"),
            Skill(profile_id=profile.id, name="Next.js", category="FRAMEWORKS", proficiency="INTERMEDIATE"),
        ]
        db.add_all(skills)

        exp1 = Experience(
            profile_id=profile.id,
            company="CloudScale Networks",
            title="Senior Backend Engineer",
            start_date="2021-04-01",
            end_date=None,
            is_current=True,
            location="San Francisco, CA",
            description=(
                "Architected high-throughput async APIs using FastAPI and PostgreSQL handling 120M daily requests. "
                "Designed low-latency Redis caching layer, decreasing p99 response times by 45%. "
                "Orchestrated microservices deployment on Kubernetes and AWS EKS using Docker."
            ),
        )
        exp2 = Experience(
            profile_id=profile.id,
            company="DataVanguard Corp",
            title="Software Engineer",
            start_date="2018-06-01",
            end_date="2021-03-31",
            is_current=False,
            location="Seattle, WA",
            description=(
                "Developed core Python backend services and automated data ingest pipelines. "
                "Migrated legacy monolithic database to PostgreSQL with zero data loss. "
                "Built automated CI/CD pipelines using Docker containers."
            ),
        )
        db.add_all([exp1, exp2])

        edu = Education(
            profile_id=profile.id,
            institution="University of Washington",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
            start_date="2014-09-01",
            end_date="2018-05-30",
            gpa=3.85,
        )
        db.add(edu)

        proj = Project(
            profile_id=profile.id,
            name="Distributed AI Inference Gateway",
            description=(
                "Engineered a high-performance LLM routing gateway in Python and FastAPI with Redis caching "
                "and Docker deployment, handling dynamic model fallback and load balancing."
            ),
            technologies=["Python", "FastAPI", "Redis", "Docker", "PostgreSQL"],
        )
        db.add(proj)
        await db.flush()
        print(f"  Added {len(skills)} skills, 2 experiences, 1 education, and 1 project.")

        # ----------------------------------------------------------------------
        # 3. Create Resume Version 1.0 (Intentionally sparse baseline)
        # ----------------------------------------------------------------------
        print("\n[Step 3] Creating Resume and Baseline Version 1.0...")
        resume = Resume(
            user_id=TEST_USER_ID,
            title="Marcus Vance - Master Cloud Backend Resume",
        )
        db.add(resume)
        await db.flush()

        v1_snapshot = {
            "summary": "Software Engineer with experience in Python and Docker development.",
            "skills": ["Python", "Docker"],  # Notice missing: FastAPI, PostgreSQL, Redis, Kubernetes, AWS
            "experience": [
                "Software Engineer at CloudScale Networks (2021-Present): Developed backend services using Python and Docker.",
                "Software Engineer at DataVanguard Corp (2018-2021): Built Python scripts and pipelines.",
            ],
            "projects": [],
        }
        v1_text = (
            "Marcus Vance\n"
            "Lead Cloud & Backend Engineer\n\n"
            "SUMMARY\n"
            "Software Engineer with experience in Python and Docker development.\n\n"
            "SKILLS\n"
            "Python, Docker\n\n"
            "EXPERIENCE\n"
            "Software Engineer at CloudScale Networks (2021-Present)\n"
            "Developed backend services using Python and Docker.\n\n"
            "Software Engineer at DataVanguard Corp (2018-2021)\n"
            "Built Python scripts and pipelines."
        )

        rv_v1 = ResumeVersion(
            resume_id=resume.id,
            version_number="v1.0",
            status="READY",
            extracted_text=v1_text,
            structured_snapshot=v1_snapshot,
            change_summary="Initial baseline resume",
            created_by=TEST_USER_ID,
        )
        db.add(rv_v1)
        await db.flush()
        resume.active_version_id = rv_v1.id
        print(f"  Created Resume Version 1.0 (ID: {rv_v1.id})")

        # ----------------------------------------------------------------------
        # 4. Add Sample Job Description
        # ----------------------------------------------------------------------
        print("\n[Step 4] Ingesting Target Job Description...")
        jd_text = """
We are seeking a Senior Backend & Cloud Engineer to join our high-scale platform team.

Responsibilities:
- Build and scale low-latency REST and streaming APIs in Python using FastAPI.
- Manage mission-critical relational datastores using PostgreSQL.
- Implement high-speed in-memory caching solutions using Redis.
- Orchestrate distributed container workloads across Kubernetes and AWS.
- Collaborate with frontend and data teams to deliver reliable software.

Requirements:
- 5+ years of software engineering experience.
- Strong proficiency in Python and FastAPI.
- Deep hands-on experience with PostgreSQL database optimization and schema design.
- Hands-on expertise with Redis caching and distributed locks.
- Production experience containerizing and deploying services with Docker and Kubernetes.

Preferred:
- Experience with AWS cloud infrastructure (EKS, RDS, S3).
- Familiarity with TypeScript and modern web architectures.
"""
        jd = JobDescription(
            user_id=TEST_USER_ID,
            title="Senior Backend & Cloud Engineer",
            company="AeroByte Technologies",
            location="Remote / San Francisco",
            raw_text=jd_text.strip(),
            status="PENDING",
        )
        db.add(jd)
        await db.flush()
        rv_v1.target_job_id = jd.id
        print(f"  Job Description Created: '{jd.title}' at {jd.company} (ID: {jd.id})")

        # ----------------------------------------------------------------------
        # 5. Extract Job Intelligence via JobService & Analyzer
        # ----------------------------------------------------------------------
        print("\n[Step 5] Extracting Job Intelligence (via JobService + Gemini/NLP)...")
        job_service = JobService(db)
        analysis = await job_service.analyze_job(jd.id, user_id=TEST_USER_ID)
        assert analysis is not None, "Job description analysis failed"
        
        # Reload job with analysis, requirements, skills
        analyzed_jd = await job_service.get_job(jd.id, user_id=TEST_USER_ID)
        assert analyzed_jd is not None
        assert len(analyzed_jd.skills) > 0, "No skills extracted from Job Description"
        print(f"  Analysis status: {analyzed_jd.status}")
        print(f"  Extracted Requirements: {len(analyzed_jd.requirements)}")
        print(f"  Extracted Skills: {[s.normalized_skill for s in analyzed_jd.skills]}")

        # ----------------------------------------------------------------------
        # 6. Calculate Baseline Job Match Score for Version 1.0
        # ----------------------------------------------------------------------
        print("\n[Step 6] Calculating Baseline Job Match Score for Resume Version 1.0...")
        job_service = JobService(db)
        match_v1 = await job_service.match_job(
            job_id=jd.id,
            payload=JobMatchRequest(
                target_type="RESUME_VERSION",
                resume_version_id=rv_v1.id,
            ),
            user_id=TEST_USER_ID,
        )
        assert match_v1 is not None, "Baseline match calculation failed"
        v1_matched = [i for i in match_v1.items if i.status == "MATCHED"]
        v1_missing = [i for i in match_v1.items if i.status == "MISSING"]
        v1_req_score = match_v1.breakdown_scores.get("required_skills", 0.0)

        print(f"  Baseline Match Overall Score (v1.0): {match_v1.overall_score}%")
        print(f"  - Required Skills Score: {v1_req_score}%")
        print(f"  - Matched Requirements: {len(v1_matched)}")
        print(f"  - Missing Requirements: {len(v1_missing)}")
        if v1_missing:
            print(f"  - Missing Requirements Sample: {[i.evidence_summary or i.explanation for i in v1_missing[:3]]}")

        # ----------------------------------------------------------------------
        # 7. Generate Tailoring Suggestions (via ResumeTailoringService)
        # ----------------------------------------------------------------------
        print("\n[Step 7] Generating Grounded Tailoring Suggestions via ResumeTailoringService...")
        # Eager load profile relations
        stmt_full_prof = (
            select(Profile)
            .options(
                selectinload(Profile.skills),
                selectinload(Profile.experiences),
                selectinload(Profile.projects),
                selectinload(Profile.educations),
                selectinload(Profile.certifications),
            )
            .where(Profile.id == profile.id)
        )
        res_full_prof = await db.execute(stmt_full_prof)
        loaded_profile = res_full_prof.scalar_one()

        tailoring_job = await resume_tailoring_service.create_tailoring_job(
            db=db,
            user_id=TEST_USER_ID,
            resume_version=rv_v1,
            job_description=analyzed_jd,
            profile=loaded_profile,
            existing_job_match=match_v1,
        )
        print(f"  Tailoring Job ID: {tailoring_job.id} (Status: {tailoring_job.status})")
        print(f"  Total Suggestions Generated: {len(tailoring_job.suggestions)}")

        # ----------------------------------------------------------------------
        # 8. Truth Guard Verification (Grounded vs Hallucinated claims)
        # ----------------------------------------------------------------------
        print("\n[Step 8] Evaluating Truth Guard Verification...")
        kb = truth_guard_service.build_candidate_knowledge_base(loaded_profile, rv_v1)

        verified_suggestions = [
            s for s in tailoring_job.suggestions if s.truth_guard_status == "VERIFIED"
        ]
        unsupported_suggestions = [
            s for s in tailoring_job.suggestions if s.truth_guard_status == "UNSUPPORTED"
        ]
        print(f"  Verified Suggestions Count: {len(verified_suggestions)}")
        print(f"  Unsupported Count from Engine: {len(unsupported_suggestions)}")
        assert len(verified_suggestions) > 0, "Expected at least 1 verified suggestion"

        for s in verified_suggestions[:3]:
            print(f"    [VERIFIED {s.suggestion_type}] {s.section}: {s.proposed_content[:70]}...")

        # Test Truth Guard on Hallucinated / Fabricated Metric
        print("\n  [Testing Truth Guard Negative constraint: Hallucinated claims]")
        fake_claim = "Engineered Quantum Neural Blockchain saving $500M and increased ARR by 8900%."
        fake_eval = truth_guard_service.validate_suggestion(
            section="EXPERIENCE",
            suggestion_type="EMPHASIZE",
            original_content="Developed Python pipelines.",
            proposed_content=fake_claim,
            knowledge_base=kb,
        )
        print(f"    Hallucination Evaluation Status: {fake_eval.status}")
        print(f"    Truth Guard Reason: {fake_eval.reason}")
        assert fake_eval.status == "UNSUPPORTED", f"Truth Guard failed to reject fake claim: {fake_eval.status}"
        print("    --> Successfully flagged and rejected unsupported hallucinated claim!")

        # ----------------------------------------------------------------------
        # 9. Accept Valid Suggestions & Create Resume Version 1.1
        # ----------------------------------------------------------------------
        print("\n[Step 9] Accepting Valid Suggestions & Creating Resume Version 1.1...")
        accepted_suggestions = verified_suggestions
        for s in accepted_suggestions:
            s.status = "ACCEPTED"

        base_snapshot = rv_v1.structured_snapshot or {}
        updated_snapshot = diff_service.apply_accepted_suggestions(base_snapshot, accepted_suggestions)
        updated_text = diff_service.render_snapshot_to_text(updated_snapshot)

        rv_v1_1 = ResumeVersion(
            resume_id=resume.id,
            version_number="v1.1",
            parent_version_id=rv_v1.id,
            target_job_id=jd.id,
            extracted_text=updated_text,
            structured_snapshot=updated_snapshot,
            change_summary="Tailored for AeroByte Senior Backend & Cloud Engineer role with verified skills",
            status="READY",
            created_by=TEST_USER_ID,
        )
        db.add(rv_v1_1)
        await db.commit()
        await db.refresh(rv_v1_1)

        print(f"  Created Version 1.1 (ID: {rv_v1_1.id})")
        print(f"  Parent Version ID: {rv_v1_1.parent_version_id} (Matches v1.0: {rv_v1_1.parent_version_id == rv_v1.id})")
        assert rv_v1_1.parent_version_id == rv_v1.id, "Version lineage broken!"

        # ----------------------------------------------------------------------
        # 10. Generate Unified Diff
        # ----------------------------------------------------------------------
        print("\n[Step 10] Generating Unified Diff between v1.0 and v1.1...")
        orig_text = rv_v1.extracted_text or ""
        text_diff = diff_service.compute_text_diff(orig_text, updated_text)
        print(f"  Similarity Ratio: {text_diff['similarity_ratio']:.1f}%")
        print(f"  Added Lines: {text_diff['added_lines']}")
        print(f"  Removed Lines: {text_diff['removed_lines']}")
        assert text_diff["added_lines"] >= 1, "No lines were added in diff"
        assert text_diff["similarity_ratio"] < 100.0, "Similarity ratio did not reflect changes"

        print("\n  --- Unified Diff Preview ---")
        for line in text_diff["unified_diff"][:15]:
            print(f"  {line}")

        # ----------------------------------------------------------------------
        # 11. Recalculate Job Match & Verify Score Comparison
        # ----------------------------------------------------------------------
        print("\n[Step 11] Recalculating Job Match for Version 1.1 (Before vs After)...")
        match_v1_1 = await job_service.match_job(
            job_id=jd.id,
            payload=JobMatchRequest(
                target_type="RESUME_VERSION",
                resume_version_id=rv_v1_1.id,
            ),
            user_id=TEST_USER_ID,
        )
        assert match_v1_1 is not None, "Post-tailoring match calculation failed"

        v1_1_matched = [i for i in match_v1_1.items if i.status == "MATCHED"]
        v1_1_missing = [i for i in match_v1_1.items if i.status == "MISSING"]
        v1_1_req_score = match_v1_1.breakdown_scores.get("required_skills", 0.0)

        score_delta = round(match_v1_1.overall_score - match_v1.overall_score, 2)
        print("\n" + "=" * 60)
        print("BEFORE VS AFTER MATCH COMPARISON:")
        print(f"  Resume Version:       v1.0  -->  v1.1")
        print(f"  Overall Score:        {match_v1.overall_score}%  -->  {match_v1_1.overall_score}%  (Delta: +{score_delta}%)")
        print(f"  Required Skills:      {v1_req_score}%  -->  {v1_1_req_score}%")
        print(f"  Matched Items:        {len(v1_matched)}  -->  {len(v1_1_matched)}")
        print(f"  Missing Items:        {len(v1_missing)}  -->  {len(v1_1_missing)}")
        print("=" * 60)

        assert match_v1_1.overall_score >= match_v1.overall_score, "Score did not improve after tailoring!"

        print("\n[ALL 11 WORKFLOW STEPS VALIDATED SUCCESSFULLY]")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_e2e_workflow())
    if not success:
        sys.exit(1)
