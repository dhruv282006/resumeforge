"""Integration tests for ResumeTailoringService, Truth Guard pipeline, and Version creation."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.models.job_requirement import JobRequirement, JobSkillRequirement
from app.models.profile import Profile
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.skill import Skill
from app.models.user import User
from app.services.diff_service import diff_service
from app.services.resume_service import DEFAULT_USER_ID
from app.services.tailoring import resume_tailoring_service


@pytest.mark.asyncio
async def test_tailoring_pipeline_and_evidence(db_session: AsyncSession):
    # 1. Setup User and Profile
    user = User(
        id=DEFAULT_USER_ID,
        email="developer@example.com",
        full_name="Alex Mercer",
    )
    db_session.add(user)

    profile = Profile(
        user_id=DEFAULT_USER_ID,
        full_name="Alex Mercer",
        headline="Full Stack Engineer",
        summary="Experienced Python engineer building web services.",
        years_of_experience=4.0,
    )
    db_session.add(profile)
    await db_session.flush()

    # Add verified skills to Profile: Python, FastAPI, Docker, PostgreSQL
    s1 = Skill(profile_id=profile.id, name="Python", category="LANGUAGES")
    s2 = Skill(profile_id=profile.id, name="FastAPI", category="FRAMEWORKS")
    s3 = Skill(profile_id=profile.id, name="Docker", category="DEVOPS")
    s4 = Skill(profile_id=profile.id, name="PostgreSQL", category="DATABASES")
    db_session.add_all([s1, s2, s3, s4])

    # 2. Setup Resume and ResumeVersion (only lists Python and Docker)
    resume = Resume(
        user_id=DEFAULT_USER_ID,
        title="Alex Mercer Resume",
    )
    db_session.add(resume)
    await db_session.flush()

    rv = ResumeVersion(
        resume_id=resume.id,
        version_number="v1.0",
        structured_snapshot={
            "summary": "Python developer working on web apps.",
            "skills": ["Python", "Docker"],
            "experience": ["Developed web services at Acme"],
        },
        extracted_text="Alex Mercer\nPython developer\nSkills: Python, Docker",
        status="READY",
    )
    db_session.add(rv)

    # 3. Setup JobDescription requesting Python, FastAPI, and PostgreSQL
    jd = JobDescription(
        user_id=DEFAULT_USER_ID,
        title="Backend Engineer",
        company="TechCorp",
        raw_text="Looking for a Backend Engineer with Python, FastAPI, and PostgreSQL experience.",
    )
    db_session.add(jd)
    await db_session.flush()

    skr1 = JobSkillRequirement(
        job_id=jd.id,
        skill_name="Python",
        normalized_skill="Python",
        importance="REQUIRED",
    )
    skr2 = JobSkillRequirement(
        job_id=jd.id,
        skill_name="FastAPI",
        normalized_skill="FastAPI",
        importance="REQUIRED",
    )
    skr3 = JobSkillRequirement(
        job_id=jd.id,
        skill_name="PostgreSQL",
        normalized_skill="PostgreSQL",
        importance="REQUIRED",
    )
    db_session.add_all([skr1, skr2, skr3])
    await db_session.commit()

    # Reload with relationships
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    prof_stmt = (
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
    profile = (await db_session.execute(prof_stmt)).scalar_one()

    jd_stmt = (
        select(JobDescription)
        .options(
            selectinload(JobDescription.skills),
            selectinload(JobDescription.requirements),
        )
        .where(JobDescription.id == jd.id)
    )
    jd = (await db_session.execute(jd_stmt)).scalar_one()
    await db_session.refresh(rv)

    # 4. Run Tailoring Service
    job = await resume_tailoring_service.create_tailoring_job(
        db=db_session,
        user_id=DEFAULT_USER_ID,
        resume_version=rv,
        job_description=jd,
        profile=profile,
    )

    assert job.status == "COMPLETED"
    assert len(job.suggestions) > 0

    # Verify that FastAPI and PostgreSQL are recommended to be added FROM PROFILE
    add_from_prof_suggestions = [
        s for s in job.suggestions if s.suggestion_type == "ADD_FROM_PROFILE" and s.section == "SKILLS"
    ]
    assert len(add_from_prof_suggestions) >= 1
    proposed_names = [s.proposed_content for s in add_from_prof_suggestions]
    assert "FastAPI" in proposed_names or "PostgreSQL" in proposed_names

    # Check Truth Guard verification status
    for s in job.suggestions:
        assert s.truth_guard_status in {"VERIFIED", "REQUIRES_REVIEW", "PARTIALLY_SUPPORTED"}
        # No hallucinated claims should be present
        assert s.truth_guard_status != "UNSUPPORTED"
