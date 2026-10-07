"""Test suite for User Authentication, Session handling, and Multi-tenant isolation."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_and_me_flow(client_with_db: AsyncClient):
    """Verify user registration, login, token retrieval, and user identity verification."""
    client = client_with_db
    unique_email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "email": unique_email,
        "full_name": "Jane Candidate",
        "password": "SecurePassword123!",
    }

    # 1. Register
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["full_name"] == "Jane Candidate"
    assert reg_data["user"]["onboarding_completed"] is False
    token = reg_data["access_token"]

    # 2. Duplicate registration should fail
    dup_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 409

    # 3. Login with valid credentials
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    token2 = login_data["access_token"]

    # 4. Login with invalid password
    bad_login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert bad_login_res.status_code == 401

    # 5. Access /me with token
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == unique_email
    assert me_data["onboarding_completed"] is False

    # 6. Complete onboarding
    ob_res = await client.post(
        "/api/v1/auth/onboarding/complete",
        json={"onboarding_completed": True},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert ob_res.status_code == 200
    assert ob_res.json()["onboarding_completed"] is True

    # 7. Verify /me now reflects onboarding_completed == True
    me_res2 = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert me_res2.status_code == 200
    assert me_res2.json()["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_multitenant_user_isolation(client_with_db: AsyncClient):
    """Ensure user A and user B have strictly isolated profiles and resumes."""
    client = client_with_db
    user_a_email = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    user_b_email = f"userb_{uuid.uuid4().hex[:8]}@example.com"

    # Register User A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "full_name": "User Alpha", "password": "PasswordAlpha123!"},
    )
    token_a = res_a.json()["access_token"]

    # Register User B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "full_name": "User Beta", "password": "PasswordBeta123!"},
    )
    token_b = res_b.json()["access_token"]

    # User A updates profile headline
    prof_update_a = await client.put(
        "/api/v1/profile",
        json={"headline": "Alpha Full Stack Lead"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert prof_update_a.status_code == 200
    assert prof_update_a.json()["headline"] == "Alpha Full Stack Lead"

    # User B fetches profile -> headline should NOT be Alpha's
    prof_b = await client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert prof_b.status_code == 200
    assert prof_b.json()["headline"] != "Alpha Full Stack Lead"

    # User A creates a resume
    resume_a = await client.post(
        "/api/v1/resumes",
        json={"title": "Alpha Resume", "target_role": "Architect"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resume_a.status_code == 201

    # User B lists resumes -> should have 0 resumes
    resumes_b = await client.get(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resumes_b.status_code == 200
    assert len(resumes_b.json()) == 0

    # User A lists resumes -> should have 1 resume
    resumes_a = await client.get(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resumes_a.status_code == 200
    assert len(resumes_a.json()) == 1
    assert resumes_a.json()[0]["title"] == "Alpha Resume"
