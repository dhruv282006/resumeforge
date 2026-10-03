"""Unit tests for DiffService unified diffs, section comparison, and suggestion application."""

from app.services.diff_service import diff_service


def test_diff_service_line_and_unified_diff():
    orig = "Line 1: Python Developer\nLine 2: Fast backend systems\nLine 3: Deployed with Docker"
    upd = "Line 1: Senior Python Engineer\nLine 2: Fast backend systems\nLine 3: Deployed with Docker\nLine 4: Monitored via Grafana"

    res = diff_service.compute_text_diff(orig, upd)
    assert res["similarity_ratio"] < 100.0
    assert res["added_lines"] >= 2  # modified line 1 + new line 4
    assert res["removed_lines"] >= 1
    assert "Senior Python Engineer" in res["unified_diff"]
    assert any(d["type"] == "ADD" for d in res["line_diffs"])


def test_diff_service_apply_suggestions_to_snapshot():
    base_snapshot = {
        "summary": "Software engineer with web experience.",
        "skills": ["Python", "FastAPI", "Docker"],
        "experience": [
            "Built backend services with Python",
        ],
    }

    class DummySuggestion:
        def __init__(self, section, suggestion_type, original, proposed):
            self.section = section
            self.suggestion_type = suggestion_type
            self.original_content = original
            self.proposed_content = proposed

    suggestions = [
        DummySuggestion(
            section="SUMMARY",
            suggestion_type="EMPHASIZE",
            original="Software engineer with web experience.",
            proposed="Senior Python Backend Engineer specializing in scalable APIs.",
        ),
        DummySuggestion(
            section="SKILLS",
            suggestion_type="ADD_FROM_PROFILE",
            original=None,
            proposed="PostgreSQL, Redis",
        ),
        DummySuggestion(
            section="SKILLS",
            suggestion_type="REORDER",
            original="Python, FastAPI, Docker",
            proposed="FastAPI, Python, Docker",
        ),
        DummySuggestion(
            section="EXPERIENCE",
            suggestion_type="REPHRASE",
            original="Built backend services with Python",
            proposed="Engineered high-concurrency microservices utilizing Python and FastAPI.",
        ),
    ]

    new_snapshot = diff_service.apply_accepted_suggestions(base_snapshot, suggestions)

    assert "Senior Python Backend Engineer" in new_snapshot["summary"]
    assert "PostgreSQL" in new_snapshot["skills"]
    assert "Redis" in new_snapshot["skills"]
    assert new_snapshot["skills"][0] == "FastAPI"
    assert any("high-concurrency microservices" in str(e) for e in new_snapshot["experience"])


def test_diff_service_render_snapshot_to_text():
    snapshot = {
        "summary": "Dedicated software developer.",
        "skills": ["Python", "SQL", "Docker"],
        "experience": ["Developed internal tools"],
        "projects": ["Task Tracker"],
    }
    rendered = diff_service.render_snapshot_to_text(snapshot)

    assert "SUMMARY" in rendered
    assert "Dedicated software developer." in rendered
    assert "SKILLS" in rendered
    assert "Python, SQL, Docker" in rendered
    assert "EXPERIENCE" in rendered
    assert "PROJECTS" in rendered
