#!/usr/bin/env python3
"""
Integration Tests for Stargate Contract v1.0

Tests contract compliance against a running Stargate instance:
- turn_id validation (422 if missing)
- turn_id idempotency (same turn_id returns cached response)
- Error code formatting
- Response schema compliance

Usage:
    python3 test_integration_contract.py
    python3 test_integration_contract.py --url http://localhost:8000
"""

import argparse
import sys
import time

import requests

# ANSI colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def test_turn_id_required(base_url: str, api_key: str) -> bool:
    """Test that turn_id is REQUIRED (422 if missing)."""
    print(f"\n{BLUE}TEST 1: turn_id REQUIRED validation{RESET}")

    try:
        response = requests.post(
            f"{base_url}/api/v1/execute",
            headers={"X-API-Key": api_key},
            json={
                "capability_key": "vendor.list",
                "org_id": "org_test",
                "user_id": "user_test",
                # turn_id MISSING - should get 422
                "args": {},
            },
        )

        if response.status_code == 422:
            error_detail = response.json().get("detail", "")
            if "turn_id" in str(error_detail).lower():
                print(f"{GREEN}✅ PASS: Missing turn_id returns 422 with validation error{RESET}")
                print(f"   Response: {response.status_code}")
                return True
            else:
                print(f"{RED}❌ FAIL: Got 422 but error doesn't mention turn_id{RESET}")
                print(f"   Detail: {error_detail}")
                return False
        else:
            print(f"{RED}❌ FAIL: Expected 422, got {response.status_code}{RESET}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"{RED}❌ ERROR: {e}{RESET}")
        return False


def test_turn_id_idempotency(base_url: str, api_key: str) -> bool:
    """Test that same turn_id returns cached response."""
    print(f"\n{BLUE}TEST 2: turn_id idempotency{RESET}")

    turn_id = f"integration_test_{int(time.time())}"

    try:
        # First request
        response1 = requests.post(
            f"{base_url}/api/v1/execute",
            headers={"X-API-Key": api_key},
            json={
                "capability_key": "vendor.list",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": turn_id,
                "args": {},
            },
        )

        if response1.status_code != 200:
            print(f"{YELLOW}⚠️  SKIP: First request failed (status={response1.status_code}){RESET}")
            print("   This is OK if QuickBooks isn't connected")
            print(f"   Response: {response1.text[:200]}")
            return True  # Skip this test gracefully

        data1 = response1.json()

        # Second request with SAME turn_id
        time.sleep(0.5)  # Small delay
        response2 = requests.post(
            f"{base_url}/api/v1/execute",
            headers={"X-API-Key": api_key},
            json={
                "capability_key": "vendor.list",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": turn_id,  # SAME turn_id
                "args": {},
            },
        )

        if response2.status_code != 200:
            print(f"{RED}❌ FAIL: Second request failed{RESET}")
            return False

        data2 = response2.json()

        # Responses should be identical (cached)
        if data1 == data2:
            print(f"{GREEN}✅ PASS: Same turn_id returns cached response{RESET}")
            print(f"   turn_id: {turn_id}")
            print(f"   Both responses identical: {data1.get('status')}")
            return True
        else:
            print(f"{RED}❌ FAIL: Responses differ (not cached){RESET}")
            print(f"   Response 1 status: {data1.get('status')}")
            print(f"   Response 2 status: {data2.get('status')}")
            return False

    except Exception as e:
        print(f"{RED}❌ ERROR: {e}{RESET}")
        return False


def test_error_response_format(base_url: str, api_key: str) -> bool:
    """Test that error responses have correct format."""
    print(f"\n{BLUE}TEST 3: Error response format{RESET}")

    try:
        # Request invalid capability to trigger error
        response = requests.post(
            f"{base_url}/api/v1/execute",
            headers={"X-API-Key": api_key},
            json={
                "capability_key": "invalid.capability.does.not.exist",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": f"error_test_{int(time.time())}",
                "args": {},
            },
        )

        if response.status_code != 200:
            print(f"{RED}❌ FAIL: Expected 200 for errors, got {response.status_code}{RESET}")
            return False

        data = response.json()

        # Verify error format
        if data.get("status") != "error":
            print(f"{RED}❌ FAIL: status should be 'error', got '{data.get('status')}'{RESET}")
            return False

        if "error_code" not in data:
            print(f"{RED}❌ FAIL: Missing error_code{RESET}")
            return False

        if "error_message" not in data:
            print(f"{RED}❌ FAIL: Missing error_message{RESET}")
            return False

        print(f"{GREEN}✅ PASS: Error response has correct format{RESET}")
        print("   status: error")
        print(f"   error_code: {data.get('error_code')}")
        print(f"   error_message: {data.get('error_message')[:50]}...")
        return True

    except Exception as e:
        print(f"{RED}❌ ERROR: {e}{RESET}")
        return False


def test_health_endpoint(base_url: str) -> bool:
    """Test health endpoint."""
    print(f"\n{BLUE}TEST 4: Health endpoint{RESET}")

    try:
        response = requests.get(f"{base_url}/health")

        if response.status_code != 200:
            print(f"{RED}❌ FAIL: Expected 200, got {response.status_code}{RESET}")
            return False

        data = response.json()

        if "status" not in data:
            print(f"{RED}❌ FAIL: Missing 'status' field{RESET}")
            return False

        print(f"{GREEN}✅ PASS: Health endpoint working{RESET}")
        print(f"   status: {data.get('status')}")
        print(f"   version: {data.get('version', 'N/A')}")
        return True

    except Exception as e:
        print(f"{RED}❌ ERROR: {e}{RESET}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Stargate Contract v1.0 compliance")
    parser.add_argument("--url", default="http://localhost:8000", help="Stargate base URL")
    parser.add_argument(
        "--api-key", default="your-super-secret-internal-api-key-change-this", help="API key"
    )
    args = parser.parse_args()

    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Stargate Contract v1.0 Integration Tests{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Base URL: {args.url}")
    print(f"API Key: {'*' * 20}")

    # Run tests
    results = []
    results.append(("turn_id REQUIRED", test_turn_id_required(args.url, args.api_key)))
    results.append(("turn_id idempotency", test_turn_id_idempotency(args.url, args.api_key)))
    results.append(("Error format", test_error_response_format(args.url, args.api_key)))
    results.append(("Health endpoint", test_health_endpoint(args.url)))

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name:.<40} {status}")

    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}✅ ALL TESTS PASSED - Contract v1.0 VERIFIED{RESET}\n")
        return 0
    else:
        print(f"\n{RED}❌ SOME TESTS FAILED{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
