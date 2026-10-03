"""API endpoint tests for Phase 3 Resume Tailoring, Suggestions, and Diffing."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.models.job_requirement import JobSkillRequirement
from app.models.profile import Profile
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.skill import Skill
from app.models.user import User
from app.services.resume_service import DEFAULT_USER_ID


@pytest.mark.asyncio
async def test_tailoring_api_full_flow(client_with_db: AsyncClient, db_session: AsyncSession):
    # 1. Seed User & Profile
    user = User(
        id=DEFAULT_USER_ID,
        email="candidate@example.com",
        full_name="Jordan Lee",
    )
    db_session.add(user)

    profile = Profile(
        user_id=DEFAULT_USER_ID,
        full_name="Jordan Lee",
        headline="Backend Engineer",
        summary="Backend developer building web services with Python and PostgreSQL.",
        years_of_experience=3.0,
    )
    db_session.add(profile)
    await db_session.flush()

    s1 = Skill(profile_id=profile.id, name="Python", category="LANGUAGES")
    s2 = Skill(profile_id=profile.id, name="FastAPI", category="FRAMEWORKS")
    s3 = Skill(profile_id=profile.id, name="Docker", category="DEVOPS")
    db_session.add_all([s1, s2, s3])

    # 2. Seed Resume & Version
    resume = Resume(
        user_id=DEFAULT_USER_ID,
        title="Backend Engineering Resume",
    )
    db_session.add(resume)
    await db_session.flush()

    rv = ResumeVersion(
        resume_id=resume.id,
        version_number="v1.0",
        structured_snapshot={
            "summary": "Junior engineer working on web backends.",
            "skills": ["Python"],
            "experience": ["Wrote Python scripts"],
        },
        extracted_text="Jordan Lee\nSkills: Python",
        status="READY",
    )
    db_session.add(rv)

    # 3. Seed Job Description
    jd = JobDescription(
        user_id=DEFAULT_USER_ID,
        title="Python Backend Developer",
        company="NexTech",
        raw_text="Requires Python, FastAPI, and Docker for high-volume microservices.",
    )
    db_session.add(jd)
    await db_session.flush()

    skr1 = JobSkillRequirement(job_id=jd.id, skill_name="Python", normalized_skill="Python", importance="REQUIRED")
    skr2 = JobSkillRequirement(job_id=jd.id, skill_name="FastAPI", normalized_skill="FastAPI", importance="REQUIRED")
    skr3 = JobSkillRequirement(job_id=jd.id, skill_name="Docker", normalized_skill="Docker", importance="REQUIRED")
    db_session.add_all([skr1, skr2, skr3])
    await db_session.commit()

    # 4. POST /api/v1/resumes/{version_id}/tailor
    tailor_res = await client_with_db.post(
        f"/api/v1/resumes/{rv.id}/tailor",
        json={"job_description_id": str(jd.id)},
    )
    assert tailor_res.status_code == 201, tailor_res.text
    job_data = tailor_res.json()
    assert job_data["status"] == "COMPLETED"
    assert len(job_data["suggestions"]) > 0
    job_id = job_data["id"]

    # 5. GET /api/v1/resumes/tailoring-jobs/{job_id}
    get_job_res = await client_with_db.get(f"/api/v1/resumes/tailoring-jobs/{job_id}")
    assert get_job_res.status_code == 200
    assert get_job_res.json()["id"] == job_id

    # 6. PATCH /api/v1/resumes/suggestions/{suggestion_id}
    first_sug = job_data["suggestions"][0]
    sug_id = first_sug["id"]
    patch_res = await client_with_db.patch(
        f"/api/v1/resumes/suggestions/{sug_id}",
        json={"status": "ACCEPTED", "user_notes": "Accepted this change"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "ACCEPTED"
    assert patch_res.json()["user_notes"] == "Accepted this change"

    # Test modifying with an invented metric -> Truth Guard must catch it!
    invented_metric_patch = await client_with_db.patch(
        f"/api/v1/resumes/suggestions/{sug_id}",
        json={
            "status": "MODIFIED",
            "proposed_content": "Increased backend revenue by 95% and saved $10M!",
        },
    )
    assert invented_metric_patch.status_code == 200
    assert invented_metric_patch.json()["truth_guard_status"] == "UNSUPPORTED"
    assert "Invented metric" in invented_metric_patch.json()["truth_guard_reason"]

    # Reset to verified content
    await client_with_db.patch(
        f"/api/v1/resumes/suggestions/{sug_id}",
        json={
            "status": "ACCEPTED",
            "proposed_content": first_sug["proposed_content"],
        },
    )

    # 7. POST /api/v1/resumes/{version_id}/apply-suggestions
    apply_res = await client_with_db.post(
        f"/api/v1/resumes/{rv.id}/apply-suggestions",
        json={
            "suggestion_ids": [sug_id],
            "change_summary": "Tailored for NexTech Python Backend Developer role",
            "trigger_match": False,
        },
    )
    assert apply_res.status_code == 201, apply_res.text
    apply_data = apply_res.json()
    assert apply_data["version_number"] == "v1.1"
    assert apply_data["accepted_count"] == 1
    assert apply_data["diff"]["added_lines"] >= 1
    new_version_id = apply_data["new_version_id"]

    # 8. GET /api/v1/resumes/{version_id}/diff/{compare_version_id}
    diff_res = await client_with_db.get(f"/api/v1/resumes/{rv.id}/diff/{new_version_id}")
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert diff_data["similarity_ratio"] < 100.0
    assert len(diff_data["line_diffs"]) > 0
