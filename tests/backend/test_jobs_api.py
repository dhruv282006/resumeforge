"""Tests for Job Description and Matching REST API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestJobsApiEndpoints:
    @pytest.mark.asyncio
    async def test_jobs_crud_and_analysis_flow(self, client_with_db: AsyncClient) -> None:
        # 1. Create Job Description
        create_res = await client_with_db.post(
            "/api/v1/jobs",
            json={
                "title": "Staff Backend Engineer",
                "company": "FastCloud",
                "location": "Remote",
                "raw_text": """About the Role:
FastCloud is hiring a Staff Backend Engineer.

Requirements:
- 5+ years of experience in Python and FastAPI development.
- Strong knowledge of PostgreSQL databases.
- Experience with Docker and microservices.

Preferred:
- Kubernetes and Redis caching experience.
""",
            },
        )
        assert create_res.status_code == 201
        job_data = create_res.json()
        job_id = job_data["id"]
        assert job_data["title"] == "Staff Backend Engineer"
        assert job_data["status"] == "DRAFT"

        # 2. Get Job Description
        get_res = await client_with_db.get(f"/api/v1/jobs/{job_id}")
        assert get_res.status_code == 200
        assert get_res.json()["company"] == "FastCloud"

        # 3. Analyze Job Description
        analyze_res = await client_with_db.post(f"/api/v1/jobs/{job_id}/analyze")
        assert analyze_res.status_code == 200
        analysis_data = analyze_res.json()
        assert analysis_data["total_requirements"] >= 3
        assert analysis_data["status"] in {"COMPLETED", "AI_PROCESSING_UNAVAILABLE"}

        # 4. List Requirements
        req_res = await client_with_db.get(f"/api/v1/jobs/{job_id}/requirements")
        assert req_res.status_code == 200
        requirements = req_res.json()
        assert len(requirements) >= 3

        # 5. Add a skill to Profile and run Match
        await client_with_db.post(
            "/api/v1/profile/skills",
            json={"name": "Python", "category": "TECHNICAL", "proficiency": "EXPERT"},
        )
        await client_with_db.post(
            "/api/v1/profile/skills",
            json={"name": "FastAPI", "category": "TECHNICAL", "proficiency": "ADVANCED"},
        )

        match_res = await client_with_db.post(
            f"/api/v1/jobs/{job_id}/match",
            json={"target_type": "PROFILE"},
        )
        assert match_res.status_code == 200
        match_data = match_res.json()
        assert "overall_score" in match_data
        assert "breakdown_scores" in match_data
        assert match_data["overall_score"] > 0
        assert len(match_data["items"]) >= 3

        # 6. Retrieve specific match
        match_id = match_data["id"]
        detail_res = await client_with_db.get(f"/api/v1/jobs/{job_id}/matches/{match_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == match_id

        # 7. List matches
        list_matches_res = await client_with_db.get(f"/api/v1/jobs/{job_id}/matches")
        assert list_matches_res.status_code == 200
        assert len(list_matches_res.json()) >= 1

        # 8. Delete job
        del_res = await client_with_db.delete(f"/api/v1/jobs/{job_id}")
        assert del_res.status_code == 204

