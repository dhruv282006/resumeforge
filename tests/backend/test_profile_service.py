"""Tests for ProfileService CRUD operations."""

from __future__ import annotations

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.profile import (
    CertificationCreate,
    EducationCreate,
    ExperienceCreate,
    ProfileUpdate,
    ProjectCreate,
    SkillCreate,
)
from app.services.profile_service import ProfileService


class TestProfileService:
    @pytest.mark.asyncio
    async def test_get_or_create_profile(self, db_session: AsyncSession) -> None:
        service = ProfileService(db_session)
        user_id = uuid.uuid4()

        profile = await service.get_or_create_profile(user_id)
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.full_name == "Candidate User"

        # Subsequent call returns the existing profile
        profile2 = await service.get_or_create_profile(user_id)
        assert profile2.id == profile.id

    @pytest.mark.asyncio
    async def test_update_profile(self, db_session: AsyncSession) -> None:
        service = ProfileService(db_session)
        user_id = uuid.uuid4()

        updated = await service.update_profile(
            ProfileUpdate(
                headline="Senior AI Engineer",
                summary="Passionate full-stack AI engineer.",
                location="Bengaluru, India",
                preferred_roles=["Lead Architect", "Senior AI Engineer"],
            ),
            user_id=user_id,
        )
        assert updated.headline == "Senior AI Engineer"
        assert updated.location == "Bengaluru, India"
        assert "Lead Architect" in updated.preferred_roles

    @pytest.mark.asyncio
    async def test_education_crud(self, db_session: AsyncSession) -> None:
        service = ProfileService(db_session)
        user_id = uuid.uuid4()

        edu = await service.create_education(
            EducationCreate(
                institution="Stanford University",
                degree="Master of Science",
                field_of_study="Computer Science",
                gpa=3.95,
            ),
            user_id=user_id,
        )
        assert edu.institution == "Stanford University"
        assert edu.gpa == 3.95

        list_edu = await service.get_educations(user_id)
        assert len(list_edu) == 1

        deleted = await service.delete_education(edu.id, user_id)
        assert deleted is True

        list_edu_after = await service.get_educations(user_id)
        assert len(list_edu_after) == 0

    @pytest.mark.asyncio
    async def test_skill_crud(self, db_session: AsyncSession) -> None:
        service = ProfileService(db_session)
        user_id = uuid.uuid4()

        skill = await service.create_skill(
            SkillCreate(
                name="Python",
                category="LANGUAGE",
                proficiency="EXPERT",
                years_of_experience=6.0,
                source="USER_PROVIDED",
                confidence=1.0,
            ),
            user_id=user_id,
        )
        assert skill.name == "Python"
        assert skill.source == "USER_PROVIDED"

        skills = await service.get_skills(user_id)
        assert len(skills) == 1
        assert skills[0].name == "Python"

