"""Service for Master Career Profile and sub-entity operations."""

from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.profile import Profile
from app.models.project import Project
from app.models.skill import Skill
from app.models.user import User
from app.schemas.profile import (
    CertificationCreate,
    CertificationUpdate,
    EducationCreate,
    EducationUpdate,
    ExperienceCreate,
    ExperienceUpdate,
    ProfileUpdate,
    ProjectCreate,
    ProjectUpdate,
    SkillCreate,
    SkillUpdate,
)
from app.services.completeness import calculate_profile_completeness


DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class ProfileService:
    """Handles CRUD logic for Profile and related career elements."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_user(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> User:
        """Ensure candidate user exists in database."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=user_id,
                email="candidate@resumeforge.local",
                full_name="Candidate User",
                role="CANDIDATE",
                is_active=True,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def get_or_create_profile(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> Profile:
        """Retrieve user profile with eager-loaded collections or create a new profile."""
        await self.get_or_create_user(user_id)

        stmt = (
            select(Profile)
            .where(Profile.user_id == user_id)
            .options(
                selectinload(Profile.educations),
                selectinload(Profile.experiences),
                selectinload(Profile.skills),
                selectinload(Profile.projects),
                selectinload(Profile.certifications),
            )
        )
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = Profile(
                user_id=user_id,
                full_name="Candidate User",
                email="candidate@resumeforge.local",
            )
            self.db.add(profile)
            await self.db.commit()

            # Re-fetch with eager loaded relationships
            result = await self.db.execute(stmt)
            profile = result.scalar_one()

        return profile

    async def update_profile(self, update_data: ProfileUpdate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Profile:
        """Update top-level profile fields."""
        profile = await self.get_or_create_profile(user_id)

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return await self.get_or_create_profile(user_id)

    async def get_completeness(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> dict:
        """Calculate and return profile completeness breakdown."""
        profile = await self.get_or_create_profile(user_id)
        return calculate_profile_completeness(profile)

    # ---------------- Education CRUD ----------------
    async def get_educations(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> List[Education]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Education).where(Education.profile_id == profile.id).order_by(Education.start_date.desc()))
        return list(result.scalars().all())

    async def create_education(self, data: EducationCreate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Education:
        profile = await self.get_or_create_profile(user_id)
        edu = Education(profile_id=profile.id, **data.model_dump())
        self.db.add(edu)
        await self.db.commit()
        await self.db.refresh(edu)
        return edu

    async def update_education(self, edu_id: uuid.UUID, data: EducationUpdate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Optional[Education]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Education).where(Education.id == edu_id, Education.profile_id == profile.id))
        edu = result.scalar_one_or_none()
        if not edu:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(edu, field, value)
        await self.db.commit()
        await self.db.refresh(edu)
        return edu

    async def delete_education(self, edu_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> bool:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Education).where(Education.id == edu_id, Education.profile_id == profile.id))
        edu = result.scalar_one_or_none()
        if not edu:
            return False
        await self.db.delete(edu)
        await self.db.commit()
        return True

    # ---------------- Experience CRUD ----------------
    async def get_experiences(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> List[Experience]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Experience).where(Experience.profile_id == profile.id).order_by(Experience.start_date.desc()))
        return list(result.scalars().all())

    async def create_experience(self, data: ExperienceCreate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Experience:
        profile = await self.get_or_create_profile(user_id)
        exp = Experience(profile_id=profile.id, **data.model_dump())
        self.db.add(exp)
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

    async def update_experience(self, exp_id: uuid.UUID, data: ExperienceUpdate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Optional[Experience]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Experience).where(Experience.id == exp_id, Experience.profile_id == profile.id))
        exp = result.scalar_one_or_none()
        if not exp:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(exp, field, value)
        await self.db.commit()
        await self.db.refresh(exp)
        return exp

    async def delete_experience(self, exp_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> bool:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Experience).where(Experience.id == exp_id, Experience.profile_id == profile.id))
        exp = result.scalar_one_or_none()
        if not exp:
            return False
        await self.db.delete(exp)
        await self.db.commit()
        return True

    # ---------------- Skills CRUD ----------------
    async def get_skills(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> List[Skill]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Skill).where(Skill.profile_id == profile.id).order_by(Skill.name.asc()))
        return list(result.scalars().all())

    async def create_skill(self, data: SkillCreate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Skill:
        profile = await self.get_or_create_profile(user_id)
        skill = Skill(profile_id=profile.id, **data.model_dump())
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def update_skill(self, skill_id: uuid.UUID, data: SkillUpdate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Optional[Skill]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Skill).where(Skill.id == skill_id, Skill.profile_id == profile.id))
        skill = result.scalar_one_or_none()
        if not skill:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(skill, field, value)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def delete_skill(self, skill_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> bool:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Skill).where(Skill.id == skill_id, Skill.profile_id == profile.id))
        skill = result.scalar_one_or_none()
        if not skill:
            return False
        await self.db.delete(skill)
        await self.db.commit()
        return True

    # ---------------- Projects CRUD ----------------
    async def get_projects(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> List[Project]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Project).where(Project.profile_id == profile.id).order_by(Project.created_at.desc()))
        return list(result.scalars().all())

    async def create_project(self, data: ProjectCreate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Project:
        profile = await self.get_or_create_profile(user_id)
        proj = Project(profile_id=profile.id, **data.model_dump())
        self.db.add(proj)
        await self.db.commit()
        await self.db.refresh(proj)
        return proj

    async def update_project(self, proj_id: uuid.UUID, data: ProjectUpdate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Optional[Project]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Project).where(Project.id == proj_id, Project.profile_id == profile.id))
        proj = result.scalar_one_or_none()
        if not proj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(proj, field, value)
        await self.db.commit()
        await self.db.refresh(proj)
        return proj

    async def delete_project(self, proj_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> bool:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Project).where(Project.id == proj_id, Project.profile_id == profile.id))
        proj = result.scalar_one_or_none()
        if not proj:
            return False
        await self.db.delete(proj)
        await self.db.commit()
        return True

    # ---------------- Certifications CRUD ----------------
    async def get_certifications(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> List[Certification]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Certification).where(Certification.profile_id == profile.id).order_by(Certification.issue_date.desc()))
        return list(result.scalars().all())

    async def create_certification(self, data: CertificationCreate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Certification:
        profile = await self.get_or_create_profile(user_id)
        cert = Certification(profile_id=profile.id, **data.model_dump())
        self.db.add(cert)
        await self.db.commit()
        await self.db.refresh(cert)
        return cert

    async def update_certification(self, cert_id: uuid.UUID, data: CertificationUpdate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Optional[Certification]:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Certification).where(Certification.id == cert_id, Certification.profile_id == profile.id))
        cert = result.scalar_one_or_none()
        if not cert:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cert, field, value)
        await self.db.commit()
        await self.db.refresh(cert)
        return cert

    async def delete_certification(self, cert_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> bool:
        profile = await self.get_or_create_profile(user_id)
        result = await self.db.execute(select(Certification).where(Certification.id == cert_id, Certification.profile_id == profile.id))
        cert = result.scalar_one_or_none()
        if not cert:
            return False
        await self.db.delete(cert)
        await self.db.commit()
        return True

