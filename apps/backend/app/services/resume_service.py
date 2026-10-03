"""Service for Resume and ResumeVersion lifecycle and version control operations."""

from __future__ import annotations

import re
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.user import User
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
    ResumeVersionClone,
    ResumeVersionCreate,
)
from app.services.extractor import get_extractor
from app.services.storage import LocalStorageProvider, StorageProvider


DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class ResumeService:
    """Handles Resume families and immutable version management."""

    def __init__(
        self,
        db: AsyncSession,
        storage: Optional[StorageProvider] = None,
    ) -> None:
        self.db = db
        self.storage = storage or LocalStorageProvider()

    async def _ensure_user(self, user_id: uuid.UUID) -> None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            user = User(
                id=user_id,
                email="candidate@resumeforge.local",
                full_name="Candidate User",
                role="CANDIDATE",
                is_active=True,
            )
            self.db.add(user)
            await self.db.commit()

    async def list_resumes(self, user_id: uuid.UUID = DEFAULT_USER_ID) -> List[Resume]:
        """List all resumes belonging to user with versions eagerly loaded."""
        await self._ensure_user(user_id)
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .options(selectinload(Resume.versions))
            .order_by(Resume.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> Optional[Resume]:
        """Get single resume with versions if owned by user."""
        stmt = (
            select(Resume)
            .where(Resume.id == resume_id, Resume.user_id == user_id)
            .options(selectinload(Resume.versions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_resume(self, data: ResumeCreate, user_id: uuid.UUID = DEFAULT_USER_ID) -> Resume:
        """Create new Resume and initialize its first version (e.g. v1.0)."""
        await self._ensure_user(user_id)
        resume = Resume(
            user_id=user_id,
            title=data.title,
            description=data.description,
            target_role=data.target_role,
            target_company=data.target_company,
            status="DRAFT",
        )
        self.db.add(resume)
        await self.db.flush()

        # Create initial version
        v_num = data.initial_version_number or "v1.0"
        initial_version = ResumeVersion(
            resume_id=resume.id,
            version_number=v_num,
            change_summary="Initial resume version created",
            status="READY",
            created_by=user_id,
        )
        self.db.add(initial_version)
        await self.db.flush()

        resume.active_version_id = initial_version.id
        await self.db.commit()

        return await self.get_resume(resume.id, user_id)  # type: ignore[return-value]

    async def update_resume(
        self, resume_id: uuid.UUID, data: ResumeUpdate, user_id: uuid.UUID = DEFAULT_USER_ID
    ) -> Optional[Resume]:
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(resume, field, value)

        await self.db.commit()
        return await self.get_resume(resume_id, user_id)

    async def delete_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> bool:
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            return False

        # Clean up stored files for all versions
        for v in resume.versions:
            if v.file_path:
                try:
                    await self.storage.delete(v.file_path)
                except Exception:
                    pass

        await self.db.delete(resume)
        await self.db.commit()
        return True

    # ---------------- Versioning Operations ----------------
    async def list_versions(self, resume_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID) -> List[ResumeVersion]:
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            return []
        stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_version(
        self, resume_id: uuid.UUID, version_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID
    ) -> Optional[ResumeVersion]:
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            return None
        stmt = select(ResumeVersion).where(
            ResumeVersion.id == version_id, ResumeVersion.resume_id == resume_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _generate_next_version_number(self, current_versions: List[ResumeVersion]) -> str:
        """Helper to suggest next version number e.g. v1.0 -> v1.1."""
        max_major, max_minor = 1, 0
        for v in current_versions:
            match = re.match(r"v?(\d+)\.(\d+)", v.version_number)
            if match:
                major, minor = int(match.group(1)), int(match.group(2))
                if major > max_major or (major == max_major and minor > max_minor):
                    max_major, max_minor = major, minor
        return f"v{max_major}.{max_minor + 1}"

    async def create_version(
        self, resume_id: uuid.UUID, data: ResumeVersionCreate, user_id: uuid.UUID = DEFAULT_USER_ID
    ) -> Optional[ResumeVersion]:
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            return None

        version = ResumeVersion(
            resume_id=resume.id,
            version_number=data.version_number,
            parent_version_id=data.parent_version_id or resume.active_version_id,
            target_job_id=data.target_job_id,
            extracted_text=data.extracted_text,
            structured_snapshot=data.structured_snapshot,
            change_summary=data.change_summary or "New resume version created",
            status="READY",
            created_by=user_id,
        )
        self.db.add(version)
        await self.db.flush()

        # Update resume updated_at
        resume.updated_at = version.created_at
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def clone_version(
        self,
        resume_id: uuid.UUID,
        source_version_id: uuid.UUID,
        clone_data: ResumeVersionClone,
        user_id: uuid.UUID = DEFAULT_USER_ID,
    ) -> Optional[ResumeVersion]:
        """Clone an existing immutable version into a new version."""
        source_version = await self.get_version(resume_id, source_version_id, user_id)
        if not source_version:
            return None

        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            return None

        new_version = ResumeVersion(
            resume_id=resume.id,
            version_number=clone_data.version_number,
            parent_version_id=source_version.id,
            target_job_id=source_version.target_job_id,
            file_path=source_version.file_path,  # reference original file if applicable
            extracted_text=source_version.extracted_text,
            structured_snapshot=source_version.structured_snapshot,
            change_summary=clone_data.change_summary or f"Cloned from {source_version.version_number}",
            status="READY",
            created_by=user_id,
        )
        self.db.add(new_version)
        await self.db.flush()

        resume.updated_at = new_version.created_at
        await self.db.commit()
        await self.db.refresh(new_version)
        return new_version

    async def activate_version(
        self, resume_id: uuid.UUID, version_id: uuid.UUID, user_id: uuid.UUID = DEFAULT_USER_ID
    ) -> Optional[Resume]:
        """Mark a specific version as the active version of the resume."""
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            return None
        version = await self.get_version(resume_id, version_id, user_id)
        if not version:
            return None

        resume.active_version_id = version.id
        await self.db.commit()
        return await self.get_resume(resume_id, user_id)

    async def upload_and_process_version(
        self,
        resume_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        user_id: uuid.UUID = DEFAULT_USER_ID,
        version_number: Optional[str] = None,
        change_summary: Optional[str] = None,
    ) -> ResumeVersion:
        """Store uploaded PDF/DOCX file, extract text, and record a new immutable version."""
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            raise ValueError(f"Resume {resume_id} not found or not owned by user.")

        # Determine version number if not provided
        v_num = version_number or self._generate_next_version_number(resume.versions)

        # 1. Upload to storage
        stored_path = await self.storage.upload(file_bytes, filename, user_id)

        # 2. Extract text using DocumentExtractor
        extracted_text = ""
        status = "READY"
        error_detail = None
        try:
            extractor = get_extractor(filename)
            extracted_text = extractor.extract(file_bytes)
        except Exception as exc:
            status = "FAILED"
            error_detail = str(exc)

        # 3. Create version record
        version = ResumeVersion(
            resume_id=resume.id,
            version_number=v_num,
            parent_version_id=resume.active_version_id,
            file_path=stored_path,
            extracted_text=extracted_text if status == "READY" else None,
            change_summary=change_summary or f"Uploaded file: {filename}",
            status=status,
            error_detail=error_detail,
            created_by=user_id,
        )
        self.db.add(version)
        await self.db.flush()

        # If success, set as active version
        if status == "READY":
            resume.active_version_id = version.id
            resume.status = "READY"

        resume.updated_at = version.created_at
        await self.db.commit()
        await self.db.refresh(version)
        return version

