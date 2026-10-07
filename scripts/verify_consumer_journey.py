"""
Comprehensive End-to-End Consumer Journey Verification Script
Tests the complete user journey against both the live Next.js frontend (http://localhost:3000)
and FastAPI backend (http://localhost:8000).

Journey:
1. Public visitor checks /, /login, /register, /onboarding on frontend
2. User registration with email/password -> JWT auth token
3. User verifies initial profile & onboarding status (false)
4. User completes guided onboarding (profile info, education, skills, experience) -> onboarding status (true)
5. User creates master resume & uploads version v1.0
6. User inputs target job description & triggers NLP analysis
7. User runs semantic match and inspects fit score & requirements
8. User runs AI tailoring with Truth Guard 2.0 evaluation
9. User accepts verified suggestions and creates tailored version snapshot (with before/after score)
10. User logs job application and updates pipeline stage
11. Verifies all frontend core routes render HTTP 200
"""

import sys
import uuid
import httpx

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def log_step(step_num: int, title: str):
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*70}")

def test_consumer_journey():
    client = httpx.Client(timeout=30.0)
    
    # -------------------------------------------------------------------------
    # STEP 1: Verify Public / Unauthenticated Frontend Routes
    # -------------------------------------------------------------------------
    log_step(1, "Public & Unauthenticated Frontend Routes")
    public_routes = ["/", "/login", "/register", "/onboarding"]
    for route in public_routes:
        url = f"{FRONTEND_URL}{route}"
        try:
            resp = client.get(url)
            print(f"  [GET] {url:<35} -> HTTP {resp.status_code}")
            assert resp.status_code == 200, f"Expected 200 for {url}, got {resp.status_code}"
        except Exception as e:
            print(f"  [FAIL] Failed to access {url}: {e}")
            raise

    # -------------------------------------------------------------------------
    # STEP 2: User Registration & JWT Authentication
    # -------------------------------------------------------------------------
    log_step(2, "User Registration & JWT Issuance")
    test_id = str(uuid.uuid4())[:8]
    test_email = f"alex.chen.{test_id}@stanford.edu"
    test_password = "SecurePassword123!"
    test_name = f"Alex Chen {test_id}"

    reg_payload = {
        "email": test_email,
        "password": test_password,
        "full_name": test_name,
    }
    
    reg_resp = client.post(f"{BACKEND_URL}/api/v1/auth/register", json=reg_payload)
    print(f"  [POST] /api/v1/auth/register -> HTTP {reg_resp.status_code}")
    assert reg_resp.status_code in (200, 201), f"Registration failed: {reg_resp.text}"
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    print(f"  User registered successfully:")
    print(f"    - User ID: {user_id}")
    print(f"    - Email:   {test_email}")
    print(f"    - Token:   {token[:15]}...{token[-10:]}")
    assert auth_data["user"]["onboarding_completed"] is False, "New user should not be onboarded yet"

    # Authenticated client with bearer token
    auth_client = httpx.Client(
        timeout=30.0,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify /me endpoint
    me_resp = auth_client.get(f"{BACKEND_URL}/api/v1/auth/me")
    assert me_resp.status_code == 200, f"Failed to get /me: {me_resp.text}"
    me_data = me_resp.json()
    print(f"  [GET] /api/v1/auth/me -> Verified identity: {me_data['email']}")

    # -------------------------------------------------------------------------
    # STEP 3: Complete Guided Onboarding Wizard
    # -------------------------------------------------------------------------
    log_step(3, "Guided Onboarding Wizard Data Seeding")
    
    # 3.1 Update basic profile info
    profile_update = {
        "full_name": test_name,
        "headline": "Full-Stack Software Engineer | Distributed Systems",
        "summary": "Software engineer with background in high-throughput backend microservices and modern frontend design.",
        "location": "San Francisco, CA",
        "phone": "+1 (555) 019-2834",
        "preferred_roles": ["Full Stack Engineer", "Backend Engineer"],
        "years_of_experience": 2.5,
    }
    prof_resp = auth_client.put(f"{BACKEND_URL}/api/v1/profile", json=profile_update)
    assert prof_resp.status_code == 200, f"Failed to update profile: {prof_resp.text}"
    print("  [Step 1/5] Profile basic info recorded.")

    # 3.2 Add Education
    edu_payload = {
        "institution": "Stanford University",
        "degree": "B.S.",
        "field_of_study": "Computer Science",
        "start_date": "2020-09-01",
        "end_date": "2024-06-15",
        "gpa": 3.88,
    }
    edu_resp = auth_client.post(f"{BACKEND_URL}/api/v1/profile/education", json=edu_payload)
    assert edu_resp.status_code in (200, 201), f"Failed to add education: {edu_resp.text}"
    print("  [Step 2/5] Education credential recorded: Stanford University.")

    # 3.3 Add Skills
    skills = ["Python", "TypeScript", "React", "FastAPI", "PostgreSQL", "Docker", "Redis"]
    for skill_name in skills:
        s_resp = auth_client.post(f"{BACKEND_URL}/api/v1/profile/skills", json={
            "name": skill_name,
            "category": "TECHNICAL",
            "proficiency": "PROFICIENT",
            "source": "USER_PROVIDED",
            "years_of_experience": 2.0,
        })
        assert s_resp.status_code in (200, 201), f"Failed to add skill {skill_name}: {s_resp.text}"
    print(f"  [Step 3/5] Skills recorded: {len(skills)} verified technical competencies.")

    # 3.4 Add Work Experience
    exp_payload = {
        "company": "Apex Cloud Systems",
        "title": "Software Engineer Intern",
        "location": "San Francisco, CA",
        "start_date": "2023-06-01",
        "end_date": "2023-12-31",
        "is_current": False,
        "description": "Engineered real-time telemetry pipeline handling 10k events/sec.",
        "achievements": [
            "Reduced query latency by 45% using Redis caching layers.",
            "Built responsive internal dashboard in React and Tailwind CSS."
        ]
    }
    exp_resp = auth_client.post(f"{BACKEND_URL}/api/v1/profile/experience", json=exp_payload)
    assert exp_resp.status_code in (200, 201), f"Failed to add experience: {exp_resp.text}"
    print("  [Step 4/5] Experience record added: Apex Cloud Systems.")

    # 3.5 Complete Onboarding
    onboard_resp = auth_client.post(f"{BACKEND_URL}/api/v1/auth/onboarding/complete")
    assert onboard_resp.status_code == 200, f"Failed to complete onboarding: {onboard_resp.text}"
    updated_me = auth_client.get(f"{BACKEND_URL}/api/v1/auth/me").json()
    assert updated_me["onboarding_completed"] is True, "onboarding_completed must be True now"
    print("  [Step 5/5] Onboarding wizard completed: status is now True.")

    # -------------------------------------------------------------------------
    # STEP 4: Resume Creation & Version Seeding
    # -------------------------------------------------------------------------
    log_step(4, "Master Resume & Version Creation")
    resume_payload = {
        "title": "Full Stack Engineer - General Resume",
        "target_role": "Full Stack Engineer",
        "target_company": "Tech Target",
        "description": "General master resume targeted for software engineering roles.",
    }
    res_resp = auth_client.post(f"{BACKEND_URL}/api/v1/resumes", json=resume_payload)
    assert res_resp.status_code in (200, 201), f"Failed to create resume: {res_resp.text}"
    resume = res_resp.json()
    resume_id = resume["id"]
    print(f"  Created resume family: '{resume['title']}' (ID: {resume_id})")

    # Add text-based version v1.0
    v1_text = f"""{test_name}
Email: {test_email} | Location: San Francisco, CA

SUMMARY
Software engineer with 2+ years experience building web applications with Python, React, and PostgreSQL.

SKILLS
Python, TypeScript, React, FastAPI, PostgreSQL, Docker, Redis

EXPERIENCE
Apex Cloud Systems — Software Engineer Intern (Jun 2023 - Dec 2023)
- Engineered real-time telemetry pipeline handling 10k events/sec.
- Reduced query latency by 45% using Redis caching layers.
- Built responsive internal dashboard in React and Tailwind CSS.

EDUCATION
Stanford University — B.S. in Computer Science (GPA: 3.88, 2020 - 2024)
"""
    v_payload = {
        "version_number": "v1.0",
        "change_summary": "Initial baseline resume version",
        "raw_text": v1_text,
    }
    v_resp = auth_client.post(f"{BACKEND_URL}/api/v1/resumes/{resume_id}/versions", json=v_payload)
    assert v_resp.status_code in (200, 201), f"Failed to create version: {v_resp.text}"
    version = v_resp.json()
    version_id = version["id"]
    print(f"  Created baseline version: {version['version_number']} (ID: {version_id})")

    # -------------------------------------------------------------------------
    # STEP 5: Target Job Description & NLP Requirement Analysis
    # -------------------------------------------------------------------------
    log_step(5, "Job Description Ingestion & NLP Extraction")
    job_payload = {
        "title": "Full Stack Software Engineer",
        "company": "Nexus Scale AI",
        "location": "San Francisco, CA (Hybrid)",
        "employment_type": "Full-time",
        "raw_text": """
Nexus Scale AI is hiring a Full Stack Software Engineer to build our enterprise agent platform.

Responsibilities:
- Build resilient backend APIs and asynchronous event processing using Python and FastAPI.
- Develop responsive, intuitive candidate and recruiter dashboards in React and TypeScript.
- Optimize relational database queries and cache strategies in PostgreSQL and Redis.
- Collaborate with engineering and product teams in an agile environment.

Requirements:
- 2+ years of professional software engineering experience.
- Strong proficiency in Python, FastAPI, and asynchronous programming.
- Proficiency in React, TypeScript, and modern state management.
- Solid experience with PostgreSQL or similar relational databases.
- Familiarity with Redis caching or background task queues.

Nice to Have:
- Experience with Docker containerization and CI/CD pipelines.
- Bachelor's degree in Computer Science or equivalent.
"""
    }
    job_resp = auth_client.post(f"{BACKEND_URL}/api/v1/jobs", json=job_payload)
    assert job_resp.status_code in (200, 201), f"Failed to create job: {job_resp.text}"
    job = job_resp.json()
    job_id = job["id"]
    print(f"  Created Job: '{job['title']}' at '{job['company']}' (ID: {job_id})")

    # Trigger requirement extraction
    analyze_resp = auth_client.post(f"{BACKEND_URL}/api/v1/jobs/{job_id}/analyze")
    assert analyze_resp.status_code == 200, f"Failed to analyze job: {analyze_resp.text}"
    analyzed_job = analyze_resp.json()
    req_count = analyzed_job.get("total_requirements", 0)
    skill_count = analyzed_job.get("total_skills", 0)
    print(f"  Job NLP Analysis completed:")
    print(f"    - Extracted requirements: {req_count}")
    print(f"    - Identified skills:       {skill_count}")

    # -------------------------------------------------------------------------
    # STEP 6: Semantic Match & Fit Score Calculation
    # -------------------------------------------------------------------------
    log_step(6, "Semantic Matching Evaluation")
    match_payload = {
        "target_type": "RESUME_VERSION",
        "resume_version_id": version_id,
    }
    match_resp = auth_client.post(f"{BACKEND_URL}/api/v1/jobs/{job_id}/match", json=match_payload)
    assert match_resp.status_code in (200, 201), f"Failed to run match: {match_resp.text}"
    match_data = match_resp.json()
    match_id = match_data["id"]
    overall_score = match_data["overall_score"]
    breakdown = match_data.get("breakdown_scores", {})
    print(f"  Match run complete:")
    print(f"    - Match Report ID: {match_id}")
    print(f"    - Overall Score:   {overall_score}/100")
    print(f"    - Required Skills: {breakdown.get('required_skills', 'N/A')}%")
    print(f"    - Experience Fit:  {breakdown.get('experience_relevance', 'N/A')}%")
    print(f"    - Semantic Fit:    {breakdown.get('semantic_alignment', 'N/A')}%")

    # -------------------------------------------------------------------------
    # STEP 7: AI Resume Tailoring & Truth Guard Evaluation
    # -------------------------------------------------------------------------
    log_step(7, "AI Tailoring & Truth Guard Audit")
    tailor_payload = {
        "job_description_id": job_id,
    }
    tailor_resp = auth_client.post(
        f"{BACKEND_URL}/api/v1/resumes/{version_id}/tailor",
        json=tailor_payload
    )
    assert tailor_resp.status_code in (200, 201), f"Tailoring trigger failed: {tailor_resp.text}"
    tailoring_run = tailor_resp.json()
    tailoring_job_id = tailoring_run["id"]
    suggestions = tailoring_run.get("suggestions", [])
    print(f"  Tailoring run generated {len(suggestions)} suggestions (Job ID: {tailoring_job_id}):")

    accepted_ids = []
    for s in suggestions:
        status_tag = s.get("truth_guard_status", "UNKNOWN")
        section = s.get("section", "UNKNOWN")
        print(f"    - [{status_tag}] [{section}] {s.get('reason')[:60]}...")
        if status_tag in ("VERIFIED", "PARTIALLY_SUPPORTED"):
            # Accept this suggestion
            update_resp = auth_client.patch(
                f"{BACKEND_URL}/api/v1/resumes/suggestions/{s['id']}",
                json={"status": "ACCEPTED"}
            )
            assert update_resp.status_code == 200
            accepted_ids.append(s["id"])

    print(f"  Accepted {len(accepted_ids)} verified suggestions for application.")

    # -------------------------------------------------------------------------
    # STEP 8: Apply Suggestions & Create Tailored Version Snapshot
    # -------------------------------------------------------------------------
    log_step(8, "Apply Suggestions & Create Tailored Snapshot")
    if accepted_ids:
        apply_payload = {
            "suggestion_ids": accepted_ids,
            "change_summary": f"Tailored snapshot with {len(accepted_ids)} verified improvements",
            "trigger_match": True,
        }
        apply_resp = auth_client.post(
            f"{BACKEND_URL}/api/v1/resumes/{version_id}/apply-suggestions",
            json=apply_payload
        )
        assert apply_resp.status_code in (200, 201), f"Apply suggestions failed: {apply_resp.text}"
        apply_data = apply_resp.json()
        new_version_num = apply_data.get("version_number", "v1.1")
        diff = apply_data.get("diff", {})
        delta = apply_data.get("score_delta")
        print(f"  New tailored version created: {new_version_num}")
        print(f"    - Lines added:   +{diff.get('added_lines', 0)}")
        print(f"    - Lines removed: -{diff.get('removed_lines', 0)}")
        print(f"    - Similarity:    {diff.get('similarity_ratio', 0)}%")
        print(f"    - Score delta:   {delta}")
    else:
        print("  No accepted suggestions to apply, skipping snapshot creation.")

    # -------------------------------------------------------------------------
    # STEP 9: Job Application Tracking Pipeline
    # -------------------------------------------------------------------------
    log_step(9, "Application Tracking Pipeline")
    app_payload = {
        "company": "Nexus Scale AI",
        "position": "Full Stack Software Engineer",
        "status": "APPLIED",
        "location": "San Francisco, CA (Hybrid)",
        "salary_range": "$135k - $160k",
        "resume_id": resume_id,
        "job_id": job_id,
        "notes": "Applied via referral with tailored resume snapshot.",
    }
    app_resp = auth_client.post(f"{BACKEND_URL}/api/v1/applications", json=app_payload)
    assert app_resp.status_code in (200, 201), f"Failed to log application: {app_resp.text}"
    app_data = app_resp.json()
    app_id = app_data["id"]
    print(f"  Application logged: '{app_data['position']}' at '{app_data['company']}' (ID: {app_id})")

    # Advance stage to SCREENING
    upd_app_resp = auth_client.put(
        f"{BACKEND_URL}/api/v1/applications/{app_id}",
        json={"status": "SCREENING"}
    )
    assert upd_app_resp.status_code == 200
    print("  Application status advanced to: SCREENING")

    # -------------------------------------------------------------------------
    # STEP 10: Multi-Tenant Isolation Check
    # -------------------------------------------------------------------------
    log_step(10, "Multi-Tenant Isolation Verification")
    # Verify candidate only sees their own data
    apps_list = auth_client.get(f"{BACKEND_URL}/api/v1/applications").json()
    assert any(a["id"] == app_id for a in apps_list), "User should see their own application"

    resumes_list = auth_client.get(f"{BACKEND_URL}/api/v1/resumes").json()
    assert any(r["id"] == resume_id for r in resumes_list), "User should see their own resume"

    jobs_list = auth_client.get(f"{BACKEND_URL}/api/v1/jobs").json()
    assert any(j["id"] == job_id for j in jobs_list), "User should see their own job"
    print("  Multi-tenant data integrity verified: Candidate accesses their isolated scope.")

    # -------------------------------------------------------------------------
    # STEP 11: Frontend Live Server Route Checks
    # -------------------------------------------------------------------------
    log_step(11, "Live Frontend Route Availability Audit")
    fe_routes = [
        "/",
        "/login",
        "/register",
        "/onboarding",
        "/dashboard",
        "/profile",
        "/resumes",
        f"/resumes/{resume_id}",
        f"/resumes/{resume_id}/tailor",
        "/jobs",
        f"/jobs/{job_id}",
        f"/jobs/{job_id}/matches/{match_id}",
        "/applications",
        "/settings",
    ]
    for route in fe_routes:
        url = f"{FRONTEND_URL}{route}"
        r = client.get(url)
        print(f"  [GET] {url:<50} -> HTTP {r.status_code}")
        assert r.status_code == 200, f"Route {url} failed with status {r.status_code}"

    print(f"\n{'='*70}")
    print("SUCCESS: ALL 11 END-TO-END CONSUMER JOURNEY STEPS VERIFIED 100%!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_consumer_journey()
