import httpx
import sys
import uuid

def test_live():
    print("=== TESTING LIVE BACKEND & AUTH API ===")
    unique_email = f"live_candidate_{uuid.uuid4().hex[:6]}@example.com"
    password = "TestPassword123!"

    # 1. Health
    r = httpx.get("http://localhost:8000/api/v1/health", timeout=10.0)
    print(f"GET /api/v1/health -> {r.status_code}")
    assert r.status_code == 200

    # 2. Register
    reg_payload = {"email": unique_email, "full_name": "Live Test Candidate", "password": password}
    r = httpx.post("http://localhost:8000/api/v1/auth/register", json=reg_payload, timeout=10.0)
    print(f"POST /api/v1/auth/register -> {r.status_code}")
    assert r.status_code == 201
    reg_data = r.json()
    token = reg_data["access_token"]
    user_id = reg_data["user"]["id"]
    print(f"  Registered User ID: {user_id}, Email: {unique_email}")

    # 3. Login
    r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"email": unique_email, "password": password}, timeout=10.0)
    print(f"POST /api/v1/auth/login -> {r.status_code}")
    assert r.status_code == 200
    token = r.json()["access_token"]

    # 4. /me
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get("http://localhost:8000/api/v1/auth/me", headers=headers, timeout=10.0)
    print(f"GET /api/v1/auth/me -> {r.status_code}, User: {r.json()['full_name']}")
    assert r.status_code == 200

    # 5. User-isolated profile
    r = httpx.get("http://localhost:8000/api/v1/profile", headers=headers, timeout=10.0)
    print(f"GET /api/v1/profile -> {r.status_code}, Name in profile: {r.json().get('full_name')}")
    assert r.status_code == 200

    print("\n=== TESTING LIVE FRONTEND PAGES (Next.js Dev Server) ===")
    pages = [
        "/",
        "/login",
        "/register",
        "/onboarding",
        "/dashboard",
        "/profile",
        "/resumes",
        "/jobs",
        "/applications",
    ]

    all_ok = True
    for p in pages:
        url = f"http://localhost:3000{p}"
        try:
            resp = httpx.get(url, timeout=30.0)
            status = resp.status_code
            print(f"GET {p:20} -> {status} {'OK' if status == 200 else 'FAIL'}")
            if status != 200:
                all_ok = False
        except Exception as e:
            print(f"GET {p:20} -> ERROR: {e}")
            all_ok = False

    if all_ok:
        print("\nALL LIVE BACKEND & FRONTEND ROUTES VERIFIED SUCCESSFULLY (HTTP 200)!")
    else:
        print("\nSOME ROUTES FAILED VERIFICATION.")
        sys.exit(1)

if __name__ == "__main__":
    test_live()
