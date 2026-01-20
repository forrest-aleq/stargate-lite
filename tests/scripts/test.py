#!/usr/bin/env python3
"""
Test script for Stargate Lite
Quick validation of the setup and basic functionality
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

BASE_URL = "http://localhost:8001"
API_KEY = os.getenv("API_SECRET_KEY", "your-super-secret-internal-api-key-change-this")


def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health", timeout=30)
    if response.status_code == 200:
        print("✅ Health check passed!")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False


def test_capabilities():
    """Test capabilities listing"""
    print("\n🔍 Testing capabilities endpoint...")
    response = requests.get(
        f"{BASE_URL}/api/v1/capabilities", headers={"X-API-Key": API_KEY}, timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} capabilities!")
        print("\nSample capabilities:")
        for key in list(data["capabilities"].keys())[:5]:
            cap = data["capabilities"][key]
            print(f"  - {key}: {cap['description']}")
        return True
    else:
        print(f"❌ Capabilities test failed: {response.status_code}")
        print(response.text)
        return False


def test_execution_without_credentials():
    """Test tool execution (will fail without credentials, but tests the flow)"""
    print("\n🔍 Testing execution endpoint (will fail without credentials)...")
    payload = {
        "capability_key": "vendor.create",
        "org_id": "test_org",
        "user_id": "test_user",
        "args": {"vendor_name": "Test Vendor", "email": "[email protected]"},
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/execute",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "error" and "No QuickBooks credentials found" in data.get("error", ""):
            print("✅ Execution flow works! (Expected credential error)")
            return True
        elif data["status"] == "success":
            print("✅ Execution succeeded! (You have credentials configured)")
            print(json.dumps(data, indent=2))
            return True

    print(f"⚠️  Unexpected response: {response.status_code}")
    print(response.text)
    return False


def test_invalid_api_key():
    """Test API key validation"""
    print("\n🔍 Testing API key validation...")
    response = requests.get(
        f"{BASE_URL}/api/v1/capabilities", headers={"X-API-Key": "wrong-key"}, timeout=30
    )
    if response.status_code == 403:
        print("✅ API key validation works!")
        return True
    else:
        print(f"❌ API key validation failed: {response.status_code}")
        return False


def test_invalid_capability():
    """Test invalid capability handling"""
    print("\n🔍 Testing invalid capability handling...")
    payload = {
        "capability_key": "invalid.capability",
        "org_id": "test_org",
        "user_id": "test_user",
        "args": {},
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/execute",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )

    if response.status_code == 404:
        print("✅ Invalid capability handling works!")
        return True
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        return False


def main():
    print("=" * 60)
    print("Stargate Lite - Test Suite")
    print("=" * 60)

    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {BASE_URL}")
        print("Make sure Stargate Lite is running:")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001")
        sys.exit(1)

    # Run tests
    tests = [
        test_health,
        test_capabilities,
        test_invalid_api_key,
        test_invalid_capability,
        test_execution_without_credentials,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test failed with exception: {e!s}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\n✅ Passed: {passed}/{total}")
    if passed == total:
        print("\n🎉 All tests passed! Stargate Lite is ready to go!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
