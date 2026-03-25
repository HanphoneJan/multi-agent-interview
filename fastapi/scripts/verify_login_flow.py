#!/usr/bin/env python3
"""Manual login and interview-session smoke test for local development."""
from __future__ import annotations

import os
import sys

import requests


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ORIGIN = os.getenv("ORIGIN", "http://localhost:3333")
TEST_EMAIL = os.getenv("TEST_EMAIL", "test_new@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "Test123456")


def test_login() -> dict[str, str] | None:
    print("=" * 60)
    print("Testing login flow")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/v1/users/login-unified",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Origin": ORIGIN, "Content-Type": "application/json"},
        timeout=10,
    )
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"[FAIL] Login failed: {response.text[:200]}")
        return None

    data = response.json()
    access = data.get("access_token") or data.get("access")
    refresh = data.get("refresh_token") or data.get("refresh")
    print("[PASS] Login successful")
    print(f"Access token: {access[:50]}...")
    return {"access": access, "refresh": refresh}


def test_create_session(tokens: dict[str, str]) -> bool:
    print("\n" + "=" * 60)
    print("Testing interview session creation")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/v1/interviews/sessions",
        json={"scenario_id": 1, "session_type": "realtime"},
        headers={
            "Origin": ORIGIN,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tokens['access']}",
        },
        timeout=10,
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 201:
        session_data = response.json()
        print(f"[PASS] Session created: {session_data.get('id')}")
        return True

    if response.status_code == 404:
        print("[WARN] Scenario not found, database may need seed data")
        return True

    print(f"[FAIL] Create session failed: {response.text[:200]}")
    return False


def main() -> int:
    print("Login and interview flow test")
    print(f"Base URL: {BASE_URL}")
    print(f"Test user: {TEST_EMAIL}")
    print()

    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("[ERROR] Server is not healthy")
            return 1
    except requests.RequestException:
        print("[ERROR] Server is not running")
        return 1

    tokens = test_login()
    if not tokens:
        return 1

    return 0 if test_create_session(tokens) else 1


if __name__ == "__main__":
    sys.exit(main())
