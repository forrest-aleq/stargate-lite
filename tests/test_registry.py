"""
Registry Test Suite
Verifies all 180 capabilities are properly mapped and callable
"""

import sys
from pathlib import Path

import pytest

# Add project root to path dynamically for test discovery
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_registry_import():
    """Test that registry can be imported"""
    try:
        from app import registry

        assert registry is not None
    except ImportError as e:
        pytest.skip(f"Dependencies not installed: {e}")


def test_capability_count():
    """Verify we have exactly 294 capabilities"""
    try:
        from app.registry import CAPABILITY_REGISTRY

        assert (
            len(CAPABILITY_REGISTRY) == 294
        ), f"Expected 294 capabilities, got {len(CAPABILITY_REGISTRY)}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_all_capabilities_have_required_fields():
    """Ensure each capability has handler, tool_name, description, service"""
    try:
        from app.registry import CAPABILITY_REGISTRY

        required_fields = ["handler", "tool_name", "description", "service", "requires_oauth"]

        for key, config in CAPABILITY_REGISTRY.items():
            for field in required_fields:
                assert field in config, f"Capability '{key}' missing field '{field}'"
                assert config[field] is not None, f"Capability '{key}' has None value for '{field}'"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_capability_handlers_are_callable():
    """Verify all handlers are actual callable functions"""
    try:
        from app.registry import CAPABILITY_REGISTRY

        for key, config in CAPABILITY_REGISTRY.items():
            handler = config["handler"]
            assert callable(handler), f"Handler for '{key}' is not callable"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_service_counts():
    """Verify endpoint counts per service"""
    try:
        from app.registry import CAPABILITY_REGISTRY

        expected_counts = {
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
            "google": 20,  # Gmail(3) + Drive(5) + Calendar(5) + Sheets(7)
            "slack": 6,
            "blandai": 8,
            "twilio": 8,
            "ibkr": 15,
            "schwab": 12,
            "microsoft": 16,  # Excel(6) + OneDrive(5) + Outlook Calendar(5)
            "ocr": 4,  # OCR utility (deepdoctection)
        }

        # Count actual capabilities per service
        actual_counts = {}
        for config in CAPABILITY_REGISTRY.values():
            service = config["service"]
            actual_counts[service] = actual_counts.get(service, 0) + 1

        # Verify counts match
        for service, expected_count in expected_counts.items():
            actual_count = actual_counts.get(service, 0)
            assert (
                actual_count == expected_count
            ), f"Service '{service}': expected {expected_count} endpoints, got {actual_count}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_oauth_requirements():
    """Verify OAuth requirements are set correctly"""
    try:
        from app.registry import CAPABILITY_REGISTRY

        # Services that should require OAuth
        oauth_services = {
            "quickbooks",
            "billcom",
            "netsuite",
            "ramp",
            "brex",
            "chase",
            "hubspot",
            "notion",
            "asana",
            "powerbi",
            "google",
            "slack",
            "schwab",
            "microsoft",
        }

        # Services that use API keys (or no auth)
        api_key_services = {
            "stripe",
            "recurly",
            "plaid",
            "mercury",
            "blandai",
            "twilio",
            "ibkr",
            "ocr",
        }

        for key, config in CAPABILITY_REGISTRY.items():
            service = config["service"]
            requires_oauth = config["requires_oauth"]

            if service in oauth_services:
                assert requires_oauth, f"'{key}' should require OAuth but doesn't"
            elif service in api_key_services:
                assert not requires_oauth, f"'{key}' should not require OAuth but does"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_unique_capability_keys():
    """Ensure no duplicate capability keys"""
    try:
        from app.registry import CAPABILITY_REGISTRY

        keys = list(CAPABILITY_REGISTRY.keys())
        unique_keys = set(keys)

        assert len(keys) == len(unique_keys), "Duplicate capability keys found"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_get_capability_function():
    """Test get_capability() helper function"""
    try:
        from app.registry import get_capability

        # Test valid capability
        vendor_create = get_capability("vendor.create")
        assert vendor_create is not None
        assert vendor_create["service"] == "quickbooks"

        # Test invalid capability
        invalid = get_capability("does.not.exist")
        assert invalid is None
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_list_capabilities_function():
    """Test list_capabilities() helper function"""
    try:
        from app.registry import list_capabilities

        capabilities = list_capabilities()
        assert isinstance(capabilities, dict)
        assert len(capabilities) == 294

        # Verify structure of returned dict
        for info in capabilities.values():
            assert "tool_name" in info
            assert "description" in info
            assert "service" in info
            assert "requires_oauth" in info
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_get_capabilities_by_service():
    """Test get_capabilities_by_service() helper function"""
    try:
        from app.registry import get_capabilities_by_service

        # Test QuickBooks
        qb_caps = get_capabilities_by_service("quickbooks")
        assert len(qb_caps) == 31

        # Test Stripe
        stripe_caps = get_capabilities_by_service("stripe")
        assert len(stripe_caps) == 61

        # Test Google (Phase 1 expansion)
        google_caps = get_capabilities_by_service("google")
        assert len(google_caps) == 20

        # Test Microsoft (Phase 1 expansion)
        microsoft_caps = get_capabilities_by_service("microsoft")
        assert len(microsoft_caps) == 16

        # Test non-existent service
        none_caps = get_capabilities_by_service("nonexistent")
        assert len(none_caps) == 0
    except ImportError:
        pytest.skip("Dependencies not installed")


if __name__ == "__main__":
    print("Running registry tests...")
    pytest.main([__file__, "-v"])
