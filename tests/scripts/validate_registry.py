#!/usr/bin/env python3
"""
Registry Validation Script
Verifies all 180 capabilities are properly mapped
Run this before deploying to ensure everything is wired correctly
"""

import sys

# Expected counts per service
EXPECTED_SERVICE_COUNTS = {
    "quickbooks": 31,
    "stripe": 61,
    "billcom": 9,
    "netsuite": 15,  # Expanded from 9
    "recurly": 9,
    "plaid": 11,
    "ramp": 5,
    "mercury": 6,
    "brex": 8,
    "chase": 8,
    "hubspot": 4,
    "notion": 10,
    "asana": 12,
    "powerbi": 10,
    "google": 20,  # Gmail(3) + Drive(5) + Calendar(5) + Sheets(7) = 20
    "slack": 6,
    "blandai": 8,
    "twilio": 8,
    "ibkr": 15,
    "schwab": 12,
    "microsoft": 16,  # Excel(6) + OneDrive(5) + Outlook Calendar(5) = 16
    "ocr": 4,  # OCR utility (deepdoctection)
}

TOTAL_EXPECTED = 294  # 251 original + 43 Phase 1


def validate_registry():
    """Validate the capability registry"""
    print("=" * 60)
    print("STARGATE LITE - Registry Validation")
    print("=" * 60)
    print()

    errors = []

    try:
        from app.registry import (
            CAPABILITY_REGISTRY,
            get_capabilities_by_service,
            get_capability,
            list_capabilities,
        )
    except ImportError as e:
        print(f"❌ FATAL: Cannot import registry: {e}")
        print("   Install dependencies: pip install -r requirements.txt")
        return False

    # Test 1: Total count
    print("Test 1: Total Capability Count")
    actual_total = len(CAPABILITY_REGISTRY)
    if actual_total == TOTAL_EXPECTED:
        print(f"✅ PASS: {actual_total} capabilities (expected {TOTAL_EXPECTED})")
    else:
        print(f"❌ FAIL: {actual_total} capabilities (expected {TOTAL_EXPECTED})")
        errors.append(f"Wrong total count: {actual_total} vs {TOTAL_EXPECTED}")
    print()

    # Test 2: Service counts
    print("Test 2: Per-Service Capability Counts")
    actual_counts = {}
    for config in CAPABILITY_REGISTRY.values():
        service = config["service"]
        actual_counts[service] = actual_counts.get(service, 0) + 1

    service_pass = True
    for service in sorted(EXPECTED_SERVICE_COUNTS.keys()):
        expected = EXPECTED_SERVICE_COUNTS[service]
        actual = actual_counts.get(service, 0)

        status = "✅" if actual == expected else "❌"
        print(f"  {status} {service:12s}: {actual:3d} endpoints (expected {expected:3d})")

        if actual != expected:
            service_pass = False
            errors.append(f"{service}: {actual} endpoints vs expected {expected}")

    if service_pass:
        print("✅ PASS: All service counts correct")
    else:
        print("❌ FAIL: Some service counts incorrect")
    print()

    # Test 3: Required fields
    print("Test 3: Required Fields Present")
    required_fields = ["handler", "tool_name", "description", "service", "requires_oauth"]
    field_errors = []

    for key, config in CAPABILITY_REGISTRY.items():
        for field in required_fields:
            if field not in config:
                field_errors.append(f"'{key}' missing field '{field}'")
            elif config[field] is None:
                field_errors.append(f"'{key}' has None value for '{field}'")

    if not field_errors:
        print("✅ PASS: All capabilities have required fields")
    else:
        print(f"❌ FAIL: {len(field_errors)} field errors")
        errors.extend(field_errors[:5])  # Show first 5
        if len(field_errors) > 5:
            print(f"   ... and {len(field_errors) - 5} more")
    print()

    # Test 4: Handlers are callable
    print("Test 4: Handlers Are Callable")
    callable_errors = []

    for key, config in CAPABILITY_REGISTRY.items():
        handler = config.get("handler")
        if not callable(handler):
            callable_errors.append(f"'{key}' handler is not callable")

    if not callable_errors:
        print(f"✅ PASS: All {actual_total} handlers are callable")
    else:
        print(f"❌ FAIL: {len(callable_errors)} non-callable handlers")
        errors.extend(callable_errors[:5])
    print()

    # Test 5: Unique keys
    print("Test 5: Unique Capability Keys")
    keys = list(CAPABILITY_REGISTRY.keys())
    unique_keys = set(keys)

    if len(keys) == len(unique_keys):
        print(f"✅ PASS: All {len(keys)} capability keys are unique")
    else:
        duplicates = len(keys) - len(unique_keys)
        print(f"❌ FAIL: {duplicates} duplicate keys found")
        errors.append(f"{duplicates} duplicate capability keys")
    print()

    # Test 6: Helper functions
    print("Test 6: Helper Functions")
    try:
        # Test get_capability
        vendor_cap = get_capability("vendor.create")
        assert vendor_cap is not None
        assert vendor_cap["service"] == "quickbooks"

        # Test list_capabilities
        caps_list = list_capabilities()
        assert len(caps_list) == actual_total

        # Test get_capabilities_by_service
        qb_caps = get_capabilities_by_service("quickbooks")
        assert len(qb_caps) == EXPECTED_SERVICE_COUNTS["quickbooks"]

        print("✅ PASS: All helper functions work correctly")
    except Exception as e:
        print(f"❌ FAIL: Helper function error: {e}")
        errors.append(f"Helper function error: {e}")
    print()

    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    if not errors:
        print("✅ ALL TESTS PASSED!")
        print(f"\n{actual_total} capabilities across 20 platforms ready for deployment")
        return True
    else:
        print(f"❌ VALIDATION FAILED - {len(errors)} error(s) found:")
        for i, error in enumerate(errors[:10], 1):
            print(f"  {i}. {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        return False


if __name__ == "__main__":
    success = validate_registry()
    sys.exit(0 if success else 1)
