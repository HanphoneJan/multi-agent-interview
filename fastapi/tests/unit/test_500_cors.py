#!/usr/bin/env python3
"""Test CORS headers on 500 error responses"""
import requests
import sys

BASE_URL = "http://localhost:8000"
ORIGIN = "http://localhost:3333"


def test_500_error_cors():
    """Test that 500 errors have CORS headers"""
    print("=" * 60)
    print("Testing CORS on 500 Error Response")
    print("=" * 60)

    # Test an endpoint that doesn't exist (should trigger 404 or 500)
    url = f"{BASE_URL}/api/v1/this-endpoint-does-not-exist"
    headers = {
        "Origin": ORIGIN,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            if "access-control" in key.lower():
                print(f"  {key}: {value}")

        ac_origin = response.headers.get("Access-Control-Allow-Origin")
        ac_credentials = response.headers.get("Access-Control-Allow-Credentials")

        print(f"\n[OK] Access-Control-Allow-Origin: {ac_origin}")
        print(f"[OK] Access-Control-Allow-Credentials: {ac_credentials}")

        if ac_origin:
            print("\n[PASS] Error response has CORS headers!")
            return True
        else:
            print("\n[FAIL] Error response missing CORS headers!")
            return False
    except Exception as e:
        print(f"\n[FAIL] Request failed: {e}")
        return False


if __name__ == "__main__":
    print("CORS 500 Error Test")
    print(f"Base URL: {BASE_URL}")
    print(f"Origin: {ORIGIN}")
    print()

    success = test_500_error_cors()
    sys.exit(0 if success else 1)
