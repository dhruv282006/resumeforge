"""Tests for deterministic profile completeness calculator."""

from __future__ import annotations

import uuid
from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.profile import Profile
from app.models.project import Project
from app.models.skill import Skill
from app.services.completeness import calculate_profile_completeness


class TestProfileCompleteness:
    def test_empty_profile_completeness(self) -> None:
        profile = Profile(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            full_name="New User",
        )
        profile.educations = []
        profile.experiences = []
        profile.skills = []
        profile.projects = []
        profile.certifications = []

        result = calculate_profile_completeness(profile)
        assert result["overall"] == 0
        assert result["sections"]["education"] == 0
        assert result["sections"]["experience"] == 0
        assert result["sections"]["skills"] == 0

    def test_fully_completed_profile(self) -> None:
        p_id = uuid.uuid4()
        profile = Profile(
            id=p_id,
            user_id=uuid.uuid4(),
            full_name="Alex Mercer",
            headline="Staff Software Engineer",
            summary="10+ years designing distributed systems.",
            email="alex@example.com",
            phone="+1234567890",
            location="San Francisco, CA",
            linkedin_url="https://linkedin.com/in/alex",
            github_url="https://github.com/alex",
        )
        profile.educations = [
            Education(id=uuid.uuid4(), profile_id=p_id, institution="MIT", degree="B.S. CS")
        ]
        profile.experiences = [
            Experience(id=uuid.uuid4(), profile_id=p_id, company="Stripe", title="Staff Engineer")
        ]
        profile.skills = [
            Skill(id=uuid.uuid4(), profile_id=p_id, name="Python"),
            Skill(id=uuid.uuid4(), profile_id=p_id, name="FastAPI"),
            Skill(id=uuid.uuid4(), profile_id=p_id, name="PostgreSQL"),
        ]
        profile.projects = [
            Project(id=uuid.uuid4(), profile_id=p_id, name="ResumeForge")
        ]
        profile.certifications = [
            Certification(id=uuid.uuid4(), profile_id=p_id, name="AWS Solutions Architect")
        ]

        result = calculate_profile_completeness(profile)
        assert result["overall"] == 100
        assert result["sections"]["personal"] == 100
        assert result["sections"]["education"] == 100
        assert result["sections"]["experience"] == 100
        assert result["sections"]["skills"] == 100
        assert result["sections"]["projects"] == 100
        assert result["sections"]["certifications"] == 100
        assert result["sections"]["links"] == 100

