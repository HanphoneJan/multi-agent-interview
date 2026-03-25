#!/usr/bin/env python3
"""
Integration Test Suite for AI Interview Agent
Tests CORS, Authentication, and Interview Session Creation
"""
import requests
import sys
import time

BASE_URL = "http://localhost:8000"
ORIGIN = "http://localhost:3333"
TEST_CREDENTIALS = {
    "email": "1195560097@qq.com",
    "password": "123456"
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

def log_warn(msg):
    print(f"[WARN] {msg}")

def test_server_running():
    log_info("Testing server connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            log_pass("Server is running")
            return True
        else:
            log_fail(f"Server returned status {response.status_code}")
            return False
    except Exception as e:
        log_fail(f"Server is not running: {e}")
        return False

def test_cors_preflight():
    log_info("Testing CORS preflight (OPTIONS)...")
    url = f"{BASE_URL}/api/v1/interviews/sessions"
    headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization",
    }
    try:
        response = requests.options(url, headers=headers, timeout=10)
        ac_origin = response.headers.get("Access-Control-Allow-Origin")
        ac_credentials = response.headers.get("Access-Control-Allow-Credentials")
        if ac_origin == ORIGIN and ac_credentials == "true":
            log_pass(f"CORS preflight OK - Origin: {ac_origin}")
            return True
        else:
            log_fail(f"CORS preflight failed - Origin: {ac_origin}, Credentials: {ac_credentials}")
            return False
    except Exception as e:
        log_fail(f"CORS preflight error: {e}")
        return False

def test_cors_on_401():
    log_info("Testing CORS on 401 response...")
    url = f"{BASE_URL}/api/v1/interviews/sessions"
    headers = {
        "Origin": ORIGIN,
        "Content-Type": "application/json",
        "Authorization": "Bearer invalid_token"
    }
    try:
        response = requests.post(url, json={"scenario_id": 1}, headers=headers, timeout=10)
        ac_origin = response.headers.get("Access-Control-Allow-Origin")
        if response.status_code == 401 and ac_origin == ORIGIN:
            log_pass("CORS on 401 OK")
            return True
        else:
            log_fail(f"CORS on 401 failed - Status: {response.status_code}, Origin: {ac_origin}")
            return False
    except Exception as e:
        log_fail(f"CORS on 401 error: {e}")
        return False

def test_login():
    log_info("Testing login...")
    url = f"{BASE_URL}/api/v1/users/login-unified"
    headers = {"Origin": ORIGIN}
    try:
        response = requests.post(url, json=TEST_CREDENTIALS, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token") or data.get("access")
            refresh_token = data.get("refresh_token") or data.get("refresh")
            if access_token and refresh_token:
                log_pass("Login successful")
                return {"access": access_token, "refresh": refresh_token}
            else:
                log_fail("Login response missing tokens")
                return None
        else:
            log_fail(f"Login failed with status {response.status_code}")
            return None
    except Exception as e:
        log_fail(f"Login error: {e}")
        return None

def test_get_user_profile(tokens):
    log_info("Testing user profile...")
    url = f"{BASE_URL}/api/v1/users/me"
    headers = {"Origin": ORIGIN, "Authorization": f"Bearer {tokens['access']}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            log_pass(f"User profile retrieved - User: {user_data.get('username')}")
            return True
        else:
            log_fail(f"Get profile failed - Status: {response.status_code}")
            return False
    except Exception as e:
        log_fail(f"Get profile error: {e}")
        return False

def test_create_session(tokens):
    log_info("Testing interview session creation...")
    url = f"{BASE_URL}/api/v1/interviews/sessions"
    headers = {"Origin": ORIGIN, "Content-Type": "application/json", "Authorization": f"Bearer {tokens['access']}"}
    data = {"scenario_id": 1, "session_type": "realtime"}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 201:
            session_data = response.json()
            session_id = session_data.get("id")
            log_pass(f"Session created successfully - ID: {session_id}")
            return session_id
        elif response.status_code == 404:
            log_warn("Scenario not found (may need seed data)")
            return None
        else:
            log_fail(f"Create session failed - Status: {response.status_code}")
            return None
    except Exception as e:
        log_fail(f"Create session error: {e}")
        return None

def print_summary():
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    warnings = sum(1 for r in results if r[0] == "WARN")
    for status, msg in results:
        print(f"[{status}] {msg}")
    print("-"*60)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Warnings: {warnings}")
    if failed == 0:
        print("\nALL TESTS PASSED!")
        return 0
    else:
        print("\nSOME TESTS FAILED!")
        return 1

def main():
    print("="*60)
    print("AI Interview Agent - Integration Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Origin: {ORIGIN}")
    print()
    if not test_server_running():
        print("\n[ERROR] Server is not running! Please start it first:")
        print("   cd fastapi && uv run uvicorn app.main:app --reload")
        return 1
    test_cors_preflight()
    test_cors_on_401()
    tokens = test_login()
    if tokens:
        test_get_user_profile(tokens)
        test_create_session(tokens)
    else:
        log_fail("Skipping authenticated tests - login failed")
    return print_summary()

if __name__ == "__main__":
    sys.exit(main())
