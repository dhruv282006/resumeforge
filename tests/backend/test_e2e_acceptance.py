"""
End-to-end acceptance test for ResumeForge Phases 0–3.

Scenario:
  - Realistic candidate: "Priya Sharma" — 5 years Python/FastAPI/PostgreSQL, Docker, React, TypeScript
  - Resume v1.0 only lists: Python, Docker (missing FastAPI, PostgreSQL, React, TypeScript)
  - Target JD: "Senior Full Stack Engineer" requiring Python, FastAPI, PostgreSQL, React, TypeScript, Docker
  - Expected flow:
      1. Tailoring engine generates ADD_FROM_PROFILE suggestions for the 4 missing skills
      2. Truth Guard marks suggestions VERIFIED (skills are present in profile)
      3. User accepts all VERIFIED suggestions
      4. Apply suggestions → new version v1.1 created
      5. Diff: added_lines >= 1, similarity_ratio < 100
      6. GET diff endpoint returns same data
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.experience import Experience
from app.models.job_description import JobDescription
from app.models.job_requirement import JobSkillRequirement
from app.models.profile import Profile
from app.models.project import Project
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.skill import Skill
from app.models.user import User
from app.services.resume_service import DEFAULT_USER_ID


@pytest.mark.asyncio
async def test_e2e_full_pipeline(client_with_db: AsyncClient, db_session: AsyncSession) -> None:
    """
    Full E2E: profile evidence → JD → tailoring → Truth Guard → version → diff.
    """

    # ──────────────────────────────────────────────
    # 1. Seed User
    # ──────────────────────────────────────────────
    user = User(
        id=DEFAULT_USER_ID,
        email="priya.sharma@example.com",
        full_name="Priya Sharma",
    )
    db_session.add(user)

    # ──────────────────────────────────────────────
    # 2. Seed Master Career Profile
    # ──────────────────────────────────────────────
    profile = Profile(
        user_id=DEFAULT_USER_ID,
        full_name="Priya Sharma",
        headline="Senior Full Stack Engineer — Python · FastAPI · React",
        summary=(
            "Results-driven engineer with 5 years of experience building high-throughput "
            "REST APIs with Python and FastAPI, PostgreSQL-backed services, and React frontends. "
            "Comfortable across the full stack from Docker-based infrastructure to TypeScript UIs."
        ),
        years_of_experience=5.0,
    )
    db_session.add(profile)
    await db_session.flush()  # get profile.id

    # Skills (full profile — the source of truth)
    profile_skills = [
        Skill(profile_id=profile.id, name="Python",     category="LANGUAGES",  proficiency="EXPERT"),
        Skill(profile_id=profile.id, name="FastAPI",    category="FRAMEWORKS", proficiency="ADVANCED"),
        Skill(profile_id=profile.id, name="PostgreSQL", category="DATABASES",  proficiency="ADVANCED"),
        Skill(profile_id=profile.id, name="React",      category="FRAMEWORKS", proficiency="INTERMEDIATE"),
        Skill(profile_id=profile.id, name="TypeScript", category="LANGUAGES",  proficiency="INTERMEDIATE"),
        Skill(profile_id=profile.id, name="Docker",     category="DEVOPS",     proficiency="ADVANCED"),
    ]
    db_session.add_all(profile_skills)

    # Experiences (with evidence that will ground Truth Guard)
    exp1 = Experience(
        profile_id=profile.id,
        company="TechCorp",
        title="Software Engineer",
        start_date="2019-07-01",
        end_date="2022-06-30",
        description=(
            "Built Python + FastAPI microservices handling 50k RPM. "
            "Optimized PostgreSQL queries, reducing p99 latency by 35%. "
            "Containerised all services with Docker; deployed on Kubernetes."
        ),
        is_current=False,
    )
    exp2 = Experience(
        profile_id=profile.id,
        company="StartupXYZ",
        title="Senior Software Engineer",
        start_date="2022-07-01",
        end_date=None,
        description=(
            "Led a team of 4 engineers building a React + TypeScript customer portal "
            "backed by a FastAPI gateway and PostgreSQL data warehouse. "
            "Introduced Docker Compose-based local dev environments, cutting onboarding time by 40%."
        ),
        is_current=True,
    )
    db_session.add_all([exp1, exp2])

    # Projects
    proj = Project(
        profile_id=profile.id,
        name="Open-Source API Gateway",
        description=(
            "Developed a lightweight API gateway in Python/FastAPI with rate-limiting, "
            "JWT auth, and a React admin dashboard using TypeScript. "
            "Packaged as a Docker image with 2k+ pulls on Docker Hub."
        ),
        technologies=["Python", "FastAPI", "React", "TypeScript", "Docker", "PostgreSQL"],
    )
    db_session.add(proj)

    # ──────────────────────────────────────────────
    # 3. Seed Resume v1.0 — intentionally sparse
    #    Only Python and Docker listed — missing FastAPI, PostgreSQL, React, TypeScript
    # ──────────────────────────────────────────────
    resume = Resume(
        user_id=DEFAULT_USER_ID,
        title="Priya Sharma — Full Stack Resume",
    )
    db_session.add(resume)
    await db_session.flush()

    rv_v1 = ResumeVersion(
        resume_id=resume.id,
        version_number="v1.0",
        status="READY",
        extracted_text=(
            "Priya Sharma\n"
            "Senior Full Stack Engineer\n\n"
            "SKILLS\n"
            "Python, Docker\n\n"
            "EXPERIENCE\n"
            "Software Engineer at TechCorp (2019–2022)\n"
            "Wrote Python scripts and managed Docker containers.\n\n"
            "Senior Software Engineer at StartupXYZ (2022–present)\n"
            "Led backend initiatives using Python."
        ),
        structured_snapshot={
            "summary": "Experienced backend engineer with Python and Docker skills.",
            "skills": ["Python", "Docker"],
            "experience": [
                "Software Engineer at TechCorp (2019–2022): Wrote Python scripts and managed Docker containers.",
                "Senior Software Engineer at StartupXYZ (2022–present): Led backend initiatives using Python.",
            ],
            "projects": [],
        },
    )
    db_session.add(rv_v1)

    # ──────────────────────────────────────────────
    # 4. Seed Job Description — Senior Full Stack Engineer
    # ──────────────────────────────────────────────
    jd = JobDescription(
        user_id=DEFAULT_USER_ID,
        title="Senior Full Stack Engineer",
        company="Horizon Labs",
        location="Remote",
        raw_text=(
            "Horizon Labs is hiring a Senior Full Stack Engineer.\n\n"
            "REQUIRED SKILLS:\n"
            "- Python (5+ years)\n"
            "- FastAPI or equivalent async Python framework\n"
            "- PostgreSQL (schema design, query optimisation)\n"
            "- React with TypeScript\n"
            "- Docker and container orchestration\n\n"
            "RESPONSIBILITIES:\n"
            "- Design and implement high-throughput REST APIs\n"
            "- Build and maintain React frontends\n"
            "- Write and optimise PostgreSQL queries\n"
            "- Containerise services with Docker\n"
        ),
    )
    db_session.add(jd)
    await db_session.flush()

    # Job skill requirements — the 6 skills the JD demands
    jd_skills = [
        JobSkillRequirement(job_id=jd.id, skill_name="Python",     normalized_skill="Python",     importance="REQUIRED"),
        JobSkillRequirement(job_id=jd.id, skill_name="FastAPI",    normalized_skill="FastAPI",    importance="REQUIRED"),
        JobSkillRequirement(job_id=jd.id, skill_name="PostgreSQL", normalized_skill="PostgreSQL", importance="REQUIRED"),
        JobSkillRequirement(job_id=jd.id, skill_name="React",      normalized_skill="React",      importance="REQUIRED"),
        JobSkillRequirement(job_id=jd.id, skill_name="TypeScript", normalized_skill="TypeScript", importance="REQUIRED"),
        JobSkillRequirement(job_id=jd.id, skill_name="Docker",     normalized_skill="Docker",     importance="REQUIRED"),
    ]
    db_session.add_all(jd_skills)
    await db_session.commit()

    # ──────────────────────────────────────────────
    # 5. TRIGGER TAILORING — POST /api/v1/resumes/{version_id}/tailor
    # ──────────────────────────────────────────────
    tailor_resp = await client_with_db.post(
        f"/api/v1/resumes/{rv_v1.id}/tailor",
        json={"job_description_id": str(jd.id)},
    )
    assert tailor_resp.status_code == 201, f"Tailor failed: {tailor_resp.text}"
    tailor_data = tailor_resp.json()

    # Tailoring job must be COMPLETED (synchronous in-process execution)
    assert tailor_data["status"] == "COMPLETED", f"Expected COMPLETED, got: {tailor_data['status']}"

    suggestions = tailor_data["suggestions"]
    assert len(suggestions) > 0, "Expected at least 1 suggestion — none generated"

    # ──────────────────────────────────────────────
    # 6. VALIDATE SUGGESTIONS
    #    ADD_FROM_PROFILE suggestions for skills missing from resume but present in profile
    # ──────────────────────────────────────────────
    add_suggestions = [s for s in suggestions if s["suggestion_type"] == "ADD_FROM_PROFILE"]
    assert len(add_suggestions) > 0, "Expected at least 1 ADD_FROM_PROFILE suggestion"

    # Collect suggested skill names
    suggested_skill_names = {s["proposed_content"] for s in add_suggestions}
    # FastAPI, PostgreSQL, React, TypeScript are in profile but NOT in resume v1.0
    expected_missing = {"FastAPI", "PostgreSQL", "React", "TypeScript"}
    found_missing = expected_missing & suggested_skill_names
    assert len(found_missing) >= 2, (
        f"Expected suggestions for missing skills {expected_missing}, "
        f"but only found: {suggested_skill_names}"
    )

    # Truth Guard must NOT mark ANY suggestion as UNSUPPORTED
    # (all are grounded in the profile's skill list)
    unsupported = [s for s in suggestions if s["truth_guard_status"] == "UNSUPPORTED"]
    assert len(unsupported) == 0, (
        f"Truth Guard marked {len(unsupported)} suggestion(s) as UNSUPPORTED — "
        f"possible hallucination: {[s['proposed_content'] for s in unsupported]}"
    )

    # Verify at least some suggestions are VERIFIED
    verified = [s for s in suggestions if s["truth_guard_status"] == "VERIFIED"]
    assert len(verified) > 0, "Expected at least 1 VERIFIED suggestion from Truth Guard"

    job_id = tailor_data["id"]

    # ──────────────────────────────────────────────
    # 7. GET tailoring job
    # ──────────────────────────────────────────────
    get_resp = await client_with_db.get(f"/api/v1/resumes/tailoring-jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == job_id

    # ──────────────────────────────────────────────
    # 8. ACCEPT all VERIFIED suggestions
    # ──────────────────────────────────────────────
    accepted_ids = []
    for sug in suggestions:
        if sug["truth_guard_status"] == "VERIFIED":
            patch_resp = await client_with_db.patch(
                f"/api/v1/resumes/suggestions/{sug['id']}",
                json={"status": "ACCEPTED"},
            )
            assert patch_resp.status_code == 200, f"Patch failed: {patch_resp.text}"
            assert patch_resp.json()["status"] == "ACCEPTED"
            accepted_ids.append(sug["id"])

    assert len(accepted_ids) > 0, "No VERIFIED suggestions were accepted"

    # ──────────────────────────────────────────────
    # 9. TRUTH GUARD NEGATIVE: invented metric must be flagged UNSUPPORTED
    # ──────────────────────────────────────────────
    first_accepted_id = accepted_ids[0]
    invented_resp = await client_with_db.patch(
        f"/api/v1/resumes/suggestions/{first_accepted_id}",
        json={
            "status": "MODIFIED",
            "proposed_content": "Increased company revenue by 9000% and saved $50M in 2 weeks!",
        },
    )
    assert invented_resp.status_code == 200
    assert invented_resp.json()["truth_guard_status"] == "UNSUPPORTED", (
        f"Expected UNSUPPORTED for invented metric, got: {invented_resp.json()['truth_guard_status']}"
    )
    assert invented_resp.json()["truth_guard_reason"] is not None

    # Reset the suggestion to the grounded version before applying
    original_content = next(s["proposed_content"] for s in suggestions if s["id"] == first_accepted_id)
    await client_with_db.patch(
        f"/api/v1/resumes/suggestions/{first_accepted_id}",
        json={"status": "ACCEPTED", "proposed_content": original_content},
    )

    # ──────────────────────────────────────────────
    # 10. APPLY ACCEPTED SUGGESTIONS → new version
    #     POST /api/v1/resumes/{version_id}/apply-suggestions
    # ──────────────────────────────────────────────
    apply_resp = await client_with_db.post(
        f"/api/v1/resumes/{rv_v1.id}/apply-suggestions",
        json={
            "suggestion_ids": accepted_ids,
            "change_summary": "Tailored for Horizon Labs Senior Full Stack Engineer role",
            "trigger_match": False,  # No pgvector in test environment
        },
    )
    assert apply_resp.status_code == 201, f"Apply failed: {apply_resp.text}"
    apply_data = apply_resp.json()

    # New version should be v1.1
    assert apply_data["version_number"] == "v1.1", (
        f"Expected v1.1, got: {apply_data['version_number']}"
    )

    # Count must match what we accepted
    assert apply_data["accepted_count"] == len(accepted_ids), (
        f"Expected {len(accepted_ids)} applied, got {apply_data['accepted_count']}"
    )

    # Diff: lines must have been added
    inline_diff = apply_data["diff"]
    assert inline_diff["added_lines"] >= 1, (
        f"Expected added_lines >= 1, got {inline_diff['added_lines']}"
    )

    # Similarity must be < 100% (resume changed)
    assert inline_diff["similarity_ratio"] < 100.0, (
        f"Expected similarity_ratio < 100, got {inline_diff['similarity_ratio']}"
    )

    new_version_id = apply_data["new_version_id"]
    assert new_version_id is not None

    # ──────────────────────────────────────────────
    # 11. GET DIFF — explicit diff endpoint
    # ──────────────────────────────────────────────
    diff_resp = await client_with_db.get(f"/api/v1/resumes/{rv_v1.id}/diff/{new_version_id}")
    assert diff_resp.status_code == 200, f"Diff GET failed: {diff_resp.text}"
    diff_data = diff_resp.json()

    assert diff_data["similarity_ratio"] < 100.0
    assert len(diff_data["line_diffs"]) > 0, "Expected non-empty line_diffs from diff endpoint"

    # The new version ID is correct in the diff response
    assert diff_data["compared_version_id"] == new_version_id

    # ──────────────────────────────────────────────
    # 12. VERIFY NEW VERSION EXISTS IN DB
    # ──────────────────────────────────────────────
    # Convert string ID from JSON response back to UUID object for SQLAlchemy query
    new_version_uuid = uuid.UUID(new_version_id)
    stmt = select(ResumeVersion).where(ResumeVersion.id == new_version_uuid)
    result = await db_session.execute(stmt)
    new_rv = result.scalar_one_or_none()
    assert new_rv is not None, "New ResumeVersion not found in database"
    assert new_rv.version_number == "v1.1"
    assert new_rv.parent_version_id == rv_v1.id

    # The new version's text must include at least one of the accepted skills
    new_text = (new_rv.extracted_text or "").lower()
    assert any(
        skill.lower() in new_text
        for skill in ["fastapi", "postgresql", "react", "typescript"]
    ), f"Expected one of the accepted skills in new version text, got:\n{new_rv.extracted_text}"
