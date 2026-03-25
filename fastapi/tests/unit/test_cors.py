#!/usr/bin/env python3
"""CORS Configuration Test Script"""
import requests
import sys

BASE_URL = "http://localhost:8000"
ORIGIN = "http://localhost:3333"


def test_cors_preflight():
    """Test CORS preflight (OPTIONS) request"""
    print("=" * 60)
    print("Testing CORS Preflight (OPTIONS) request")
    print("=" * 60)

    url = f"{BASE_URL}/api/v1/interviews/sessions"
    headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization",
    }

    try:
        response = requests.options(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            if "access-control" in key.lower():
                print(f"  {key}: {value}")

        # Check required CORS headers
        ac_origin = response.headers.get("Access-Control-Allow-Origin")
        ac_methods = response.headers.get("Access-Control-Allow-Methods")
        ac_headers = response.headers.get("Access-Control-Allow-Headers")
        ac_credentials = response.headers.get("Access-Control-Allow-Credentials")

        print(f"\n[OK] Access-Control-Allow-Origin: {ac_origin}")
        print(f"[OK] Access-Control-Allow-Methods: {ac_methods}")
        print(f"[OK] Access-Control-Allow-Headers: {ac_headers}")
        print(f"[OK] Access-Control-Allow-Credentials: {ac_credentials}")

        if ac_origin == ORIGIN or ac_origin == "*":
            print("\n[PASS] Preflight CORS headers are correct!")
            return True
        else:
            print(f"\n[FAIL] Preflight failed: Origin mismatch (expected {ORIGIN})")
            return False
    except Exception as e:
        print(f"\n[FAIL] Preflight request failed: {e}")
        return False


def test_cors_actual_request():
    """Test actual POST request with CORS headers"""
    print("\n" + "=" * 60)
    print("Testing CORS on actual POST request")
    print("=" * 60)

    url = f"{BASE_URL}/api/v1/interviews/sessions"
    headers = {
        "Origin": ORIGIN,
        "Content-Type": "application/json",
    }
    data = {
        "scenario_id": 1,
        "session_type": "realtime"
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            if "access-control" in key.lower():
                print(f"  {key}: {value}")

        ac_origin = response.headers.get("Access-Control-Allow-Origin")
        ac_credentials = response.headers.get("Access-Control-Allow-Credentials")

        print(f"\n[OK] Access-Control-Allow-Origin: {ac_origin}")
        print(f"[OK] Access-Control-Allow-Credentials: {ac_credentials}")

        if ac_origin == ORIGIN or ac_origin == "*":
            print("\n[PASS] Actual request CORS headers are correct!")
            return True
        else:
            print(f"\n[FAIL] Actual request failed: Origin mismatch (expected {ORIGIN})")
            return False
    except Exception as e:
        print(f"\n[FAIL] Actual request failed: {e}")
        return False


def test_health_endpoint():
    """Test simple health endpoint for CORS"""
    print("\n" + "=" * 60)
    print("Testing CORS on Health Endpoint (GET)")
    print("=" * 60)

    url = f"{BASE_URL}/health"
    headers = {
        "Origin": ORIGIN,
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            if "access-control" in key.lower():
                print(f"  {key}: {value}")

        ac_origin = response.headers.get("Access-Control-Allow-Origin")

        print(f"\n[OK] Access-Control-Allow-Origin: {ac_origin}")

        if ac_origin == ORIGIN or ac_origin == "*":
            print("\n[PASS] Health endpoint CORS headers are correct!")
            return True
        else:
            print(f"\n[FAIL] Health endpoint failed: Origin mismatch")
            return False
    except Exception as e:
        print(f"\n[FAIL] Health request failed: {e}")
        return False


def test_server_running():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return True
    except:
        return False


if __name__ == "__main__":
    print("CORS Test Script")
    print(f"Base URL: {BASE_URL}")
    print(f"Origin: {ORIGIN}")
    print()

    if not test_server_running():
        print("[ERROR] Server is not running! Please start the FastAPI server first.")
        print("   Run: cd fastapi && uv run uvicorn app.main:app --reload")
        sys.exit(1)

    results = []
    results.append(("Preflight (OPTIONS)", test_cors_preflight()))
    results.append(("Health (GET)", test_health_endpoint()))
    results.append(("POST /sessions", test_cors_actual_request()))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    if all(r[1] for r in results):
        print("\n[ALL PASSED] All CORS tests passed!")
        sys.exit(0)
    else:
        print("\n[SOME FAILED] Some CORS tests failed!")
        sys.exit(1)
