#!/usr/bin/env python3
"""
ResumeForge – scripts/check_services.py
========================================
Health-check script for all local development services.
Uses only the Python standard library (no external dependencies).

Exit codes:
  0 – all services healthy
  1 – one or more services failed / unreachable

Usage:
  python scripts/check_services.py
"""

import json
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------
@dataclass
class ServiceResult:
    name: str
    host: str
    port: int | str
    status: str          # "✔ OK" | "✗ FAIL"
    detail: str


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------
def check_tcp(host: str, port: int, timeout: float = 3.0) -> tuple[bool, str]:
    """Try to open a TCP connection to host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"TCP connection to {host}:{port} succeeded"
    except OSError as exc:
        return False, str(exc)


def check_http(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """Perform a GET request and expect a 2xx response."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(512).decode("utf-8", errors="replace")
            # Try to extract a meaningful status field from JSON
            try:
                data = json.loads(body)
                detail = f"HTTP {resp.status} – {data}"
            except json.JSONDecodeError:
                detail = f"HTTP {resp.status} – {body[:80]}"
            return True, detail
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return False, str(exc.reason)
    except OSError as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Services to check
# ---------------------------------------------------------------------------
def build_checks() -> list[tuple[str, str, int | str, Callable[[], tuple[bool, str]]]]:
    """Return list of (name, host, port, check_fn) tuples."""
    return [
        (
            "PostgreSQL",
            "localhost",
            5432,
            lambda: check_tcp("localhost", 5432),
        ),
        (
            "Redis",
            "localhost",
            6379,
            lambda: check_tcp("localhost", 6379),
        ),
        (
            "MailHog SMTP",
            "localhost",
            1025,
            lambda: check_tcp("localhost", 1025),
        ),
        (
            "MailHog Web UI",
            "localhost",
            8025,
            lambda: check_http("http://localhost:8025"),
        ),
        (
            "Backend API",
            "localhost",
            8000,
            lambda: check_http("http://localhost:8000/api/v1/health"),
        ),
        (
            "Frontend",
            "localhost",
            3000,
            lambda: check_tcp("localhost", 3000),
        ),
    ]


# ---------------------------------------------------------------------------
# Table renderer
# ---------------------------------------------------------------------------
def render_table(results: list[ServiceResult]) -> None:
    col_name   = max(len(r.name)   for r in results) + 2
    col_host   = max(len(r.host)   for r in results) + 2
    col_port   = max(len(str(r.port)) for r in results) + 2
    col_status = 10
    col_detail = 60

    header = (
        f"{'Service':<{col_name}}"
        f"{'Host':<{col_host}}"
        f"{'Port':<{col_port}}"
        f"{'Status':<{col_status}}"
        f"{'Detail'}"
    )
    sep = "-" * (col_name + col_host + col_port + col_status + col_detail)

    print()
    print("ResumeForge – Service Health Check")
    print(sep)
    print(header)
    print(sep)
    for r in results:
        detail_trunc = (r.detail[:col_detail - 3] + "...") if len(r.detail) > col_detail else r.detail
        print(
            f"{r.name:<{col_name}}"
            f"{r.host:<{col_host}}"
            f"{str(r.port):<{col_port}}"
            f"{r.status:<{col_status}}"
            f"{detail_trunc}"
        )
    print(sep)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    checks = build_checks()
    results: list[ServiceResult] = []

    for name, host, port, check_fn in checks:
        ok, detail = check_fn()
        results.append(ServiceResult(
            name=name,
            host=host,
            port=port,
            status="✔ OK  " if ok else "✗ FAIL",
            detail=detail,
        ))

    render_table(results)

    failed = [r for r in results if r.status.startswith("✗")]
    if failed:
        names = ", ".join(r.name for r in failed)
        print(f"❌  {len(failed)} service(s) unhealthy: {names}")
        print("    Make sure all containers are running:  make up\n")
        return 1

    print(f"✅  All {len(results)} services are healthy!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
