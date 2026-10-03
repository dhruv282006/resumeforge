"""Tests for MatchingEngine, scoring methodology, evidence attribution, and weight sensitivity."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.experience import Experience
from app.models.project import Project
from app.services.jd_analyzer import JobDescriptionAnalyzer
from app.services.matching_engine import MatchingConfig, MatchingEngine, MatchingWeights
from app.services.profile_service import DEFAULT_USER_ID
from tests.fixtures.job_matching.dataset import EVALUATION_DATASET


class TestMatchingEngine:
    @pytest.mark.asyncio
    async def test_strong_match_evaluation_case(self, db_session: AsyncSession) -> None:
        case = EVALUATION_DATASET["strong_match"]
        analyzer = JobDescriptionAnalyzer(db_session, llm_provider=None)
        engine = MatchingEngine(db_session)

        # 1. Create Job and analyze
        job = JobDescription(
            user_id=DEFAULT_USER_ID,
            title=case["job"]["title"],
            company=case["job"]["company"],
            raw_text=case["job"]["raw_text"],
        )
        db_session.add(job)
        await db_session.commit()
        await analyzer.analyze_job(job)

        # 2. Create Candidate Profile
        cand = case["candidate"]
        profile = Profile(
            user_id=DEFAULT_USER_ID,
            full_name=cand["full_name"],
            headline=cand["headline"],
            years_of_experience=cand["years_of_experience"],
        )
        db_session.add(profile)
        await db_session.flush()

        for sk in cand["skills"]:
            db_session.add(Skill(profile_id=profile.id, name=sk["name"], category=sk["category"], proficiency=sk.get("proficiency")))

        for exp in cand["experiences"]:
            db_session.add(Experience(profile_id=profile.id, company=exp["company"], title=exp["title"], description=exp["description"], achievements=exp.get("achievements", [])))

        for proj in cand["projects"]:
            db_session.add(Project(profile_id=profile.id, name=proj["name"], technologies=proj["technologies"], description=proj["description"]))

        await db_session.commit()

        # 3. Run Matching
        match = await engine.compute_match(job, profile)
        assert match.overall_score >= 70.0
        assert match.status == "COMPLETED"

        # Check breakdown scores exist
        assert "required_skills" in match.breakdown_scores
        assert "semantic_alignment" in match.breakdown_scores
        assert match.breakdown_scores["required_skills"] >= 70.0

        # Check evidence attribution ("WHY?")
        matched_items = [it for it in match.items if it.status == "MATCHED"]
        assert len(matched_items) >= 2
        for m in matched_items:
            assert m.matched_entity_name is not None
            assert m.evidence_source in {"USER_PROVIDED", "RESUME_PARSED"}
            assert m.explanation is not None

    @pytest.mark.asyncio
    async def test_weak_match_evaluation_case(self, db_session: AsyncSession) -> None:
        case = EVALUATION_DATASET["weak_match"]
        analyzer = JobDescriptionAnalyzer(db_session, llm_provider=None)
        engine = MatchingEngine(db_session)

        # 1. Create iOS Job
        job = JobDescription(
            user_id=DEFAULT_USER_ID,
            title=case["job"]["title"],
            company=case["job"]["company"],
            raw_text=case["job"]["raw_text"],
        )
        db_session.add(job)
        await db_session.commit()
        await analyzer.analyze_job(job)

        # 2. Create ML/Python Profile
        cand = case["candidate"]
        profile = Profile(
            user_id=DEFAULT_USER_ID,
            full_name=cand["full_name"],
            headline=cand["headline"],
            years_of_experience=cand["years_of_experience"],
        )
        db_session.add(profile)
        await db_session.flush()

        for sk in cand["skills"]:
            db_session.add(Skill(profile_id=profile.id, name=sk["name"], category=sk["category"]))

        await db_session.commit()

        # 3. Run Matching
        match = await engine.compute_match(job, profile)
        # Should have low match score because Swift/iOS/SwiftUI are missing
        assert match.overall_score <= 60.0

        # Verify MISSING classification for absent required skills
        missing_items = [it for it in match.items if it.status == "MISSING"]
        assert len(missing_items) >= 1

    @pytest.mark.asyncio
    async def test_weight_sensitivity_and_persistence(self, db_session: AsyncSession) -> None:
        analyzer = JobDescriptionAnalyzer(db_session, llm_provider=None)
        engine = MatchingEngine(db_session)

        job = JobDescription(
            user_id=DEFAULT_USER_ID,
            title="Python Developer",
            raw_text="Requirements:\n- Python programming.\n- Docker deployment.",
        )
        db_session.add(job)
        await db_session.commit()
        await analyzer.analyze_job(job)

        profile = Profile(user_id=DEFAULT_USER_ID, full_name="Test Dev")
        db_session.add(profile)
        await db_session.flush()
        db_session.add(Skill(profile_id=profile.id, name="Python"))
        await db_session.commit()

        # Weights emphasizing required skills
        weights_skill_heavy = MatchingWeights(
            required_skills=0.70,
            preferred_skills=0.05,
            experience_relevance=0.05,
            project_relevance=0.05,
            semantic_alignment=0.15,
        )
        match1 = await engine.compute_match(job, profile, custom_weights=weights_skill_heavy)

        # Weights emphasizing experience/projects (where candidate has none)
        weights_exp_heavy = MatchingWeights(
            required_skills=0.10,
            preferred_skills=0.05,
            experience_relevance=0.40,
            project_relevance=0.35,
            semantic_alignment=0.10,
        )
        match2 = await engine.compute_match(job, profile, custom_weights=weights_exp_heavy)

        # Scores should differ based on weights
        assert match1.overall_score != match2.overall_score

        # Verify weights were persisted in JobMatch.score_weights
        assert match1.score_weights["required_skills"] == 0.70
        assert match2.score_weights["required_skills"] == 0.10

