"""Endpoints for Master Career Profile and sub-entities."""

from __future__ import annotations

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.profile import (
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
    EducationCreate,
    EducationResponse,
    EducationUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    ProfileCompletenessResponse,
    ProfileResponse,
    ProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)
from app.services.profile_service import ProfileService

router = APIRouter()


def get_profile_service(db: AsyncSession = Depends(get_db)) -> ProfileService:
    return ProfileService(db)


# ---------------- Master Profile Endpoints ----------------
@router.get("", response_model=ProfileResponse)
async def get_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Retrieve candidate master career profile."""
    return await service.get_or_create_profile(user_id)  # type: ignore[return-value]


@router.put("", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Update candidate master career profile fields."""
    return await service.update_profile(payload, user_id)  # type: ignore[return-value]


@router.get("/completeness", response_model=ProfileCompletenessResponse)
async def get_profile_completeness(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileCompletenessResponse:
    """Calculate deterministic completeness score for candidate profile."""
    data = await service.get_completeness(user_id)
    return ProfileCompletenessResponse(**data)


# ---------------- Education Endpoints ----------------
@router.get("/education", response_model=List[EducationResponse])
async def list_educations(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> List[EducationResponse]:
    return await service.get_educations(user_id)  # type: ignore[return-value]


@router.post("/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def create_education(
    payload: EducationCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> EducationResponse:
    return await service.create_education(payload, user_id)  # type: ignore[return-value]


@router.put("/education/{id}", response_model=EducationResponse)
async def update_education(
    id: uuid.UUID,
    payload: EducationUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> EducationResponse:
    edu = await service.update_education(id, payload, user_id)
    if not edu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found")
    return edu  # type: ignore[return-value]


@router.delete("/education/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_education(
    id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    deleted = await service.delete_education(id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found")


# ---------------- Experience Endpoints ----------------
@router.get("/experience", response_model=List[ExperienceResponse])
async def list_experiences(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> List[ExperienceResponse]:
    return await service.get_experiences(user_id)  # type: ignore[return-value]


@router.post("/experience", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(
    payload: ExperienceCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ExperienceResponse:
    return await service.create_experience(payload, user_id)  # type: ignore[return-value]


@router.put("/experience/{id}", response_model=ExperienceResponse)
async def update_experience(
    id: uuid.UUID,
    payload: ExperienceUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ExperienceResponse:
    exp = await service.update_experience(id, payload, user_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience record not found")
    return exp  # type: ignore[return-value]


@router.delete("/experience/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_experience(
    id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    deleted = await service.delete_experience(id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience record not found")


# ---------------- Skills Endpoints ----------------
@router.get("/skills", response_model=List[SkillResponse])
async def list_skills(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> List[SkillResponse]:
    return await service.get_skills(user_id)  # type: ignore[return-value]


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> SkillResponse:
    return await service.create_skill(payload, user_id)  # type: ignore[return-value]


@router.put("/skills/{id}", response_model=SkillResponse)
async def update_skill(
    id: uuid.UUID,
    payload: SkillUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> SkillResponse:
    skill = await service.update_skill(id, payload, user_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill record not found")
    return skill  # type: ignore[return-value]


@router.delete("/skills/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_skill(
    id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    deleted = await service.delete_skill(id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill record not found")


# ---------------- Projects Endpoints ----------------
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> List[ProjectResponse]:
    return await service.get_projects(user_id)  # type: ignore[return-value]


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProjectResponse:
    return await service.create_project(payload, user_id)  # type: ignore[return-value]


@router.put("/projects/{id}", response_model=ProjectResponse)
async def update_project(
    id: uuid.UUID,
    payload: ProjectUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProjectResponse:
    proj = await service.update_project(id, payload, user_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project record not found")
    return proj  # type: ignore[return-value]


@router.delete("/projects/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_project(
    id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    deleted = await service.delete_project(id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project record not found")


# ---------------- Certifications Endpoints ----------------
@router.get("/certifications", response_model=List[CertificationResponse])
async def list_certifications(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> List[CertificationResponse]:
    return await service.get_certifications(user_id)  # type: ignore[return-value]


@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def create_certification(
    payload: CertificationCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> CertificationResponse:
    return await service.create_certification(payload, user_id)  # type: ignore[return-value]


@router.put("/certifications/{id}", response_model=CertificationResponse)
async def update_certification(
    id: uuid.UUID,
    payload: CertificationUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> CertificationResponse:
    cert = await service.update_certification(id, payload, user_id)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification record not found")
    return cert  # type: ignore[return-value]


@router.delete("/certifications/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_certification(
    id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    deleted = await service.delete_certification(id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification record not found")
