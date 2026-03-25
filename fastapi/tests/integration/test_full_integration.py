#!/usr/bin/env python3
"""
Full Integration Test for AI Interview Agent
Auto-registers user and tests complete flow
"""
import requests
import sys
import time
import random

BASE_URL = "http://localhost:8000"
ORIGIN = "http://localhost:3333"

# Generate unique test user
TEST_ID = random.randint(1000, 9999)
TEST_USER = {
    "username": f"testuser{TEST_ID}",
    "email": f"test{TEST_ID}@example.com",
    "password": "testpass123",
    "phone": f"138{TEST_ID:06d}"
}

results = []

def log_pass(msg):
    print(f"[PASS] {msg}")
    results.append(("PASS", msg))

def log_fail(msg):
    print(f"[FAIL] {msg}")
    results.append(("FAIL", msg))

def log_info(msg):
    print(f"[INFO] {msg}")

def test_server():
    log_info("Testing server connectivity...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            log_pass("Server is running")
            return True
    except:
        pass
    log_fail("Server is not running")
    return False

def test_cors_preflight():
    log_info("Testing CORS preflight...")
    headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization",
    }
    try:
        r = requests.options(f"{BASE_URL}/api/v1/interviews/sessions", headers=headers, timeout=10)
        if r.headers.get("Access-Control-Allow-Origin") == ORIGIN:
            log_pass("CORS preflight working")
            return True
    except Exception as e:
        log_fail(f"CORS error: {e}")
    return False

def test_cors_on_error():
    log_info("Testing CORS on 401 error...")
    headers = {"Origin": ORIGIN, "Authorization": "Bearer invalid"}
    try:
        r = requests.post(f"{BASE_URL}/api/v1/interviews/sessions", json={}, headers=headers, timeout=10)
        if r.status_code == 401 and r.headers.get("Access-Control-Allow-Origin") == ORIGIN:
            log_pass("CORS on 401 error working")
            return True
    except Exception as e:
        log_fail(f"CORS error test failed: {e}")
    return False

def test_register():
    log_info(f"Registering test user: {TEST_USER['email']}...")
    try:
        r = requests.post(f"{BASE_URL}/api/v1/users/register", json=TEST_USER, timeout=10)
        if r.status_code == 201:
            data = r.json()
            log_pass("User registered successfully")
            return {
                "access": data.get("access_token") or data.get("access"),
                "refresh": data.get("refresh_token") or data.get("refresh")
            }
        else:
            log_fail(f"Registration failed: {r.status_code}")
    except Exception as e:
        log_fail(f"Registration error: {e}")
    return None

def test_login():
    log_info("Testing login...")
    try:
        r = requests.post(f"{BASE_URL}/api/v1/users/login-unified", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }, timeout=10)
        if r.status_code == 200:
            data = r.json()
            log_pass("Login successful")
            return {
                "access": data.get("access_token") or data.get("access"),
                "refresh": data.get("refresh_token") or data.get("refresh")
            }
        else:
            log_fail(f"Login failed: {r.status_code}")
    except Exception as e:
        log_fail(f"Login error: {e}")
    return None

def test_profile(tokens):
    log_info("Testing user profile...")
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    try:
        r = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers, timeout=10)
        if r.status_code == 200:
            log_pass(f"Profile retrieved: {r.json().get('username')}")
            return True
    except Exception as e:
        log_fail(f"Profile error: {e}")
    return False

def test_create_session(tokens):
    log_info("Testing interview session creation...")
    headers = {"Authorization": f"Bearer {tokens['access']}", "Content-Type": "application/json"}
    data = {"scenario_id": 1, "session_type": "realtime"}
    try:
        r = requests.post(f"{BASE_URL}/api/v1/interviews/sessions", json=data, headers=headers, timeout=10)
        if r.status_code == 201:
            session_id = r.json().get("id")
            log_pass(f"Session created: ID {session_id}")
            return session_id
        elif r.status_code == 404:
            log_fail("Scenario not found - need to seed database")
        else:
            log_fail(f"Create session failed: {r.status_code}")
    except Exception as e:
        log_fail(f"Create session error: {e}")
    return None

def print_summary():
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    for status, msg in results:
        print(f"[{status}] {msg}")
    print("-"*60)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    return 0 if failed == 0 else 1

def main():
    print("="*60)
    print("AI Interview Agent - Full Integration Test")
    print("="*60)

    if not test_server():
        print("\n[ERROR] Start server: cd fastapi && uv run uvicorn app.main:app --reload")
        return 1

    test_cors_preflight()
    test_cors_on_error()

    tokens = test_register()
    if not tokens:
        tokens = test_login()

    if tokens:
        test_profile(tokens)
        test_create_session(tokens)

    return print_summary()

if __name__ == "__main__":
    sys.exit(main())
