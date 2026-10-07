"""Tests for Applications REST API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestApplicationsApiEndpoints:
    @pytest.mark.asyncio
    async def test_application_crud_flow(self, client_with_db: AsyncClient) -> None:
        # 1. Create application
        create_payload = {
            "company": "Anthropic",
            "position": "Research Engineer",
            "status": "APPLIED",
            "location": "San Francisco, CA",
            "salary_range": "$250,000 - $320,000",
            "notes": "Applied via referral link",
        }
        res_create = await client_with_db.post("/api/v1/applications", json=create_payload)
        assert res_create.status_code == 201
        app = res_create.json()
        app_id = app["id"]
        assert app["company"] == "Anthropic"
        assert app["position"] == "Research Engineer"
        assert app["status"] == "APPLIED"

        # 2. List applications
        res_list = await client_with_db.get("/api/v1/applications")
        assert res_list.status_code == 200
        apps = res_list.json()
        assert any(a["id"] == app_id for a in apps)

        # 3. Get single application
        res_get = await client_with_db.get(f"/api/v1/applications/{app_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == app_id

        # 4. Update status to INTERVIEWING
        update_payload = {"status": "INTERVIEWING", "notes": "Technical screen scheduled"}
        res_put = await client_with_db.put(f"/api/v1/applications/{app_id}", json=update_payload)
        assert res_put.status_code == 200
        updated = res_put.json()
        assert updated["status"] == "INTERVIEWING"
        assert updated["notes"] == "Technical screen scheduled"

        # 5. Get application stats
        res_stats = await client_with_db.get("/api/v1/applications/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["total"] >= 1
        assert stats["interviewing"] >= 1

        # 6. Delete application
        res_del = await client_with_db.delete(f"/api/v1/applications/{app_id}")
        assert res_del.status_code == 204

        # 7. Confirm deleted
        res_get_del = await client_with_db.get(f"/api/v1/applications/{app_id}")
        assert res_get_del.status_code == 404
