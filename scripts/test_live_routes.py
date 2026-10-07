import httpx

routes = [
    "/",
    "/login",
    "/register",
    "/dashboard",
    "/profile",
    "/resumes",
    "/jobs",
    "/applications",
]

client_no_redirect = httpx.Client(base_url="http://localhost:3000", follow_redirects=False, timeout=30.0)
client_with_redirect = httpx.Client(base_url="http://localhost:3000", follow_redirects=True, timeout=30.0)

print(f"{'Route':16} | {'Expected':12} | {'Actual':12} | {'Status':8}")
print("-" * 54)

for r in routes:
    expected = "307 -> 200" if r == "/" else "200"
    res_direct = client_no_redirect.get(r)
    res_final = client_with_redirect.get(r)

    if r == "/":
        actual = f"{res_direct.status_code} -> {res_final.status_code}"
        passed = (res_direct.status_code == 307 and res_final.status_code == 200)
    else:
        actual = str(res_direct.status_code)
        passed = (res_direct.status_code == 200)

    status = "PASS" if passed else "FAIL"
    print(f"{r:16} | {expected:12} | {actual:12} | {status:8}")

