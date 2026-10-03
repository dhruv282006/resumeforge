"""Tests for Job Description analysis pipeline."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.services.jd_analyzer import DeterministicJDExtractor, JobDescriptionAnalyzer
from app.services.profile_service import DEFAULT_USER_ID


class TestDeterministicJDExtractor:
    def test_section_and_item_parsing(self) -> None:
        extractor = DeterministicJDExtractor()
        raw_text = """About the Role:
We are looking for a Software Engineer.

Responsibilities:
- Build and maintain REST APIs using FastAPI and Python.
- Collaborate with frontend teams.

Requirements:
- 5+ years of experience in backend development.
- Bachelor's degree in Computer Science or related field.
- Strong proficiency with PostgreSQL and Redis.

Preferred Qualifications:
- Experience with Kubernetes and Docker.
- AWS certification is a plus.
"""
        items = extractor.parse_sections_and_items(raw_text)
        assert len(items) >= 5

        categories = {item["category"] for item in items}
        assert "SKILL" in categories or "EXPERIENCE" in categories
        assert "EDUCATION" in categories

        # Check years extraction
        exp_item = next(it for it in items if it.get("min_experience_years") == 5.0)
        assert exp_item["min_experience_years"] == 5.0

        # Check importance tagging
        pref_items = [it for it in items if it["importance"] == "PREFERRED"]
        assert len(pref_items) >= 1


class TestJobDescriptionAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_job_creates_requirements_and_skills(self, db_session: AsyncSession) -> None:
        analyzer = JobDescriptionAnalyzer(db_session, llm_provider=None)

        job = JobDescription(
            user_id=DEFAULT_USER_ID,
            title="Senior Backend Engineer",
            company="CloudTech",
            raw_text="""Requirements:
- 4+ years of Python software engineering experience.
- Deep expertise in FastAPI and PostgreSQL.
- Experience with Docker containerization.
Preferred:
- Kubernetes knowledge.
""",
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        analysis = await analyzer.analyze_job(job)
        assert analysis.status in {"COMPLETED", "AI_PROCESSING_UNAVAILABLE"}
        assert analysis.total_requirements >= 3
        assert analysis.total_skills >= 2

        # Verify job.status updated
        assert job.status == "PARSED"
        assert len(job.requirements) >= 3
        assert len(job.skills) >= 2

