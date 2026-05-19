"""
Registry Test Suite
Verifies all capabilities are properly mapped and callable
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
    """Verify we have expected number of capabilities (614+)"""
    try:
        from app.registry import ALL_CAPABILITIES

        # Validate unfiltered registry — CAPABILITY_REGISTRY may be smaller
        # depending on which env vars are set (key-gated services)
        assert (
            len(ALL_CAPABILITIES) >= 600
        ), f"Expected at least 600 capabilities, got {len(ALL_CAPABILITIES)}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_all_capabilities_have_required_fields():
    """Ensure each capability has handler, tool_name, description, service"""
    try:
        from app.registry import ALL_CAPABILITIES

        required_fields = ["handler", "tool_name", "description", "service", "requires_oauth"]

        for key, config in ALL_CAPABILITIES.items():
            for field in required_fields:
                assert field in config, f"Capability '{key}' missing field '{field}'"
                assert config[field] is not None, f"Capability '{key}' has None value for '{field}'"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_capability_handlers_are_callable():
    """Verify all handlers are actual callable functions"""
    try:
        from app.registry import ALL_CAPABILITIES

        for key, config in ALL_CAPABILITIES.items():
            handler = config["handler"]
            assert callable(handler), f"Handler for '{key}' is not callable"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_service_counts():
    """Verify endpoint counts per service (minimum thresholds)"""
    try:
        from app.registry import ALL_CAPABILITIES

        # Validate against unfiltered registry — key-gated services may be
        # hidden in CAPABILITY_REGISTRY depending on env vars
        minimum_counts = {
            "quickbooks": 70,
            "stripe": 60,
            "billcom": 20,
            "netsuite": 20,
            "plaid": 10,
            "mercury": 5,
            "brex": 5,
            "chase": 5,
            "hubspot": 15,
            "notion": 10,
            "asana": 10,
            "powerbi": 10,
            "google": 30,
            "slack": 10,
            "microsoft": 15,
            "ocr": 5,
            "sage_intacct": 40,
            "xero": 60,
            "gusto": 15,
            "shopify": 15,
            "square": 15,
            "docusign": 10,
            "airtable": 10,
        }

        # Count actual capabilities per service
        actual_counts: dict[str, int] = {}
        for config in ALL_CAPABILITIES.values():
            service = config["service"]
            actual_counts[service] = actual_counts.get(service, 0) + 1

        # Verify minimum counts are met
        for service, min_count in minimum_counts.items():
            actual_count = actual_counts.get(service, 0)
            assert (
                actual_count >= min_count
            ), f"Service '{service}': expected at least {min_count} endpoints, got {actual_count}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_oauth_requirements():
    """Verify OAuth requirements are set correctly for known services"""
    try:
        from app.registry import ALL_CAPABILITIES

        # Services that should require OAuth
        oauth_services = {
            "quickbooks",
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
            "microsoft",
            "gusto",
            "shopify",
            "square",
            "docusign",
            "airtable",
            "sage_intacct",
            "xero",
            "linear",
            "stripe",  # Stripe Connect OAuth
        }

        # Services that use API keys, session auth, or no auth
        api_key_services = {
            "recurly",
            "plaid",
            "mercury",
            "ocr",
            "billcom",  # Session-based auth, not OAuth
        }

        for key, config in ALL_CAPABILITIES.items():
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
        from app.registry import ALL_CAPABILITIES

        keys = list(ALL_CAPABILITIES.keys())
        unique_keys = set(keys)

        assert len(keys) == len(unique_keys), "Duplicate capability keys found"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_get_capability_function():
    """Test get_capability() helper function"""
    try:
        from app.registry import get_capability

        # Test with always-available capability (not key-gated)
        ocr_extract = get_capability("ocr.text.extract")
        assert ocr_extract is not None
        assert ocr_extract["service"] == "ocr"

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
        # Runtime list depends on env vars; just verify it returns something
        assert len(capabilities) >= 1

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

        # Test always-available services (not key-gated)
        ocr_caps = get_capabilities_by_service("ocr")
        assert len(ocr_caps) >= 5

        workflow_caps = get_capabilities_by_service("workflow")
        assert len(workflow_caps) >= 1

        financial_calc_caps = get_capabilities_by_service("financial_calculator")
        assert len(financial_calc_caps) >= 5

        # Test non-existent service
        none_caps = get_capabilities_by_service("nonexistent")
        assert len(none_caps) == 0
    except ImportError:
        pytest.skip("Dependencies not installed")


if __name__ == "__main__":
    print("Running registry tests...")
    pytest.main([__file__, "-v"])
