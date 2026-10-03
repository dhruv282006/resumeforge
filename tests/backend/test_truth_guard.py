"""Comprehensive tests for Truth Guard Service claim validation and hallucination rejection."""

import uuid
import pytest
from app.services.truth_guard import truth_guard_service


class DummyProfile:
    def __init__(self):
        self.years_of_experience = 3.5
        self.summary = "Full stack software engineer with experience building web applications and APIs."
        self.headline = "Software Engineer"
        self.skills = [
            type("Skill", (), {"id": uuid.uuid4(), "name": "Python", "category": "LANGUAGES"})(),
            type("Skill", (), {"id": uuid.uuid4(), "name": "FastAPI", "category": "FRAMEWORKS"})(),
            type("Skill", (), {"id": uuid.uuid4(), "name": "PostgreSQL", "category": "DATABASES"})(),
            type("Skill", (), {"id": uuid.uuid4(), "name": "Docker", "category": "DEVOPS"})(),
        ]
        self.experiences = [
            type(
                "Exp",
                (),
                {
                    "id": uuid.uuid4(),
                    "title": "Software Engineer",
                    "company": "Acme Corp",
                    "description": "Built REST APIs with FastAPI and PostgreSQL serving 10000 daily users.",
                    "responsibilities": ["Refactored database queries reducing latency by 25%"],
                    "achievements": [],
                },
            )()
        ]
        self.projects = [
            type(
                "Proj",
                (),
                {
                    "id": uuid.uuid4(),
                    "title": "TaskFlow",
                    "description": "Task management platform built with Python and Docker",
                    "technologies": ["Python", "Docker"],
                },
            )()
        ]
        self.educations = []
        self.certifications = []


def test_truth_guard_rejects_invented_metrics():
    """Truth Guard must flag suggestions with metrics not found in candidate records as UNSUPPORTED."""
    profile = DummyProfile()
    kb = truth_guard_service.build_candidate_knowledge_base(profile)

    # Candidate profile has 25% latency reduction, NOT 80% or $5M
    evaluation = truth_guard_service.validate_suggestion(
        section="EXPERIENCE",
        suggestion_type="REPHRASE",
        original_content="Refactored database queries reducing latency by 25%",
        proposed_content="Refactored database queries reducing latency by 80% and saving $5M annually.",
        knowledge_base=kb,
    )

    assert evaluation.status == "UNSUPPORTED"
    assert "Invented metric" in evaluation.reason
    assert any("80%" in str(c.unsupported_metrics) for c in evaluation.claims)


def test_truth_guard_rejects_unverified_skills():
    """Truth Guard must reject introduction of technologies the candidate has no evidence for."""
    profile = DummyProfile()
    kb = truth_guard_service.build_candidate_knowledge_base(profile)

    # Candidate knows Python, FastAPI, Docker, PostgreSQL. Candidate does NOT know Rust or Kubernetes
    evaluation = truth_guard_service.validate_suggestion(
        section="SKILLS",
        suggestion_type="ADD_FROM_PROFILE",
        original_content=None,
        proposed_content="Rust, Kubernetes, and Snowflake",
        knowledge_base=kb,
    )

    assert evaluation.status == "UNSUPPORTED"
    assert "Invented technology/skill" in evaluation.reason


def test_truth_guard_verifies_grounded_suggestion():
    """Truth Guard must mark suggestions containing genuine candidate facts as VERIFIED."""
    profile = DummyProfile()
    kb = truth_guard_service.build_candidate_knowledge_base(profile)

    # Grounded in candidate's real skill and experience at Acme Corp
    evaluation = truth_guard_service.validate_suggestion(
        section="EXPERIENCE",
        suggestion_type="EMPHASIZE",
        original_content="Built REST APIs with FastAPI",
        proposed_content="Architected high-throughput REST APIs using FastAPI and PostgreSQL at Acme Corp.",
        knowledge_base=kb,
    )

    assert evaluation.status == "VERIFIED"
    assert len(evaluation.supported_evidence) > 0


def test_truth_guard_verifies_structural_operations():
    """Structural operations like REORDER or REMOVE should always pass verification."""
    profile = DummyProfile()
    kb = truth_guard_service.build_candidate_knowledge_base(profile)

    eval_reorder = truth_guard_service.validate_suggestion(
        section="SKILLS",
        suggestion_type="REORDER",
        original_content="Python, Docker, FastAPI",
        proposed_content="FastAPI, Python, Docker",
        knowledge_base=kb,
    )
    assert eval_reorder.status == "VERIFIED"

    eval_remove = truth_guard_service.validate_suggestion(
        section="SKILLS",
        suggestion_type="REMOVE",
        original_content="ObsoleteSkill",
        proposed_content="",
        knowledge_base=kb,
    )
    assert eval_remove.status == "VERIFIED"


def test_truth_guard_verifies_existing_metrics():
    """Truth Guard accepts metrics that match candidate's actual records."""
    profile = DummyProfile()
    kb = truth_guard_service.build_candidate_knowledge_base(profile)

    # 25% is in candidate's experience
    evaluation = truth_guard_service.validate_suggestion(
        section="EXPERIENCE",
        suggestion_type="REPHRASE",
        original_content="Refactored database queries reducing latency by 25%",
        proposed_content="Optimized complex PostgreSQL queries, successfully reducing query latency by 25%.",
        knowledge_base=kb,
    )

    assert evaluation.status == "VERIFIED"
