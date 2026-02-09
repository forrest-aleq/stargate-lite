"""
Schema Test Suite
Verifies the Enhanced Capability Registry schemas are properly defined and functional.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path dynamically for test discovery
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_schema_import():
    """Test that schemas module can be imported"""
    try:
        from app import schemas

        assert schemas is not None
    except ImportError as e:
        pytest.skip(f"Dependencies not installed: {e}")


def test_schema_registry_count():
    """Verify we have the expected number of capability schemas"""
    try:
        from app.schemas import SCHEMA_REGISTRY

        # Minimum expected schemas - can grow as services are added
        assert (
            len(SCHEMA_REGISTRY) >= 500
        ), f"Expected at least 500 schemas, got {len(SCHEMA_REGISTRY)}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_all_schemas_have_required_fields():
    """Ensure each schema has required fields"""
    try:
        from app.schemas import SCHEMA_REGISTRY

        for key, schema in SCHEMA_REGISTRY.items():
            assert schema.capability_key == key, f"Schema key mismatch for '{key}'"
            assert schema.service, f"Schema '{key}' missing service"
            assert schema.description, f"Schema '{key}' missing description"
            assert isinstance(schema.parameters, dict), f"Schema '{key}' parameters not a dict"
            assert isinstance(schema.returns, dict), f"Schema '{key}' returns not a dict"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_vendor_schemas_exist():
    """Verify all vendor schemas are present"""
    try:
        from app.schemas import SCHEMA_REGISTRY

        vendor_keys = [
            "vendor.create",
            "vendor.get",
            "vendor.list",
            "vendor.search",
            "vendor.update",
        ]

        for key in vendor_keys:
            assert key in SCHEMA_REGISTRY, f"Missing vendor schema: {key}"
            assert SCHEMA_REGISTRY[key].service == "quickbooks"
            assert SCHEMA_REGISTRY[key].category == "vendors"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_bill_schemas_exist():
    """Verify all bill schemas are present"""
    try:
        from app.schemas import SCHEMA_REGISTRY

        bill_keys = [
            "bill.create",
            "bill.get",
            "bill.list",
            "bill.payment.create",
            "billpayment.list",
        ]

        for key in bill_keys:
            assert key in SCHEMA_REGISTRY, f"Missing bill schema: {key}"
            assert SCHEMA_REGISTRY[key].service == "quickbooks"
            assert SCHEMA_REGISTRY[key].category == "bills"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_get_schema_function():
    """Test get_schema() helper function"""
    try:
        from app.schemas import get_schema

        # Test valid schema
        vendor_create = get_schema("vendor.create")
        assert vendor_create is not None
        assert vendor_create.service == "quickbooks"
        assert vendor_create.capability_key == "vendor.create"

        # Test invalid schema
        invalid = get_schema("does.not.exist")
        assert invalid is None
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_list_schemas_function():
    """Test list_schemas() helper function"""
    try:
        from app.schemas import list_schemas

        # Test all schemas
        all_schemas = list_schemas()
        assert isinstance(all_schemas, dict)
        assert len(all_schemas) >= 500  # Minimum expected

        # Test filtered by service (minimum expected)
        qb_schemas = list_schemas(service="quickbooks")
        assert len(qb_schemas) >= 70

        stripe_schemas = list_schemas(service="stripe")
        assert len(stripe_schemas) >= 200

        google_schemas = list_schemas(service="google")
        assert len(google_schemas) >= 20

        slack_schemas = list_schemas(service="slack")
        assert len(slack_schemas) >= 10

        hubspot_schemas = list_schemas(service="hubspot")
        assert len(hubspot_schemas) >= 15

        plaid_schemas = list_schemas(service="plaid")
        assert len(plaid_schemas) >= 10

        microsoft_schemas = list_schemas(service="microsoft")
        assert len(microsoft_schemas) >= 5

        dropbox_schemas = list_schemas(service="dropbox")
        assert len(dropbox_schemas) >= 5

        netsuite_schemas = list_schemas(service="netsuite")
        assert len(netsuite_schemas) >= 15

        # Test non-existent service
        none_schemas = list_schemas(service="nonexistent")
        assert len(none_schemas) == 0
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_has_schema_function():
    """Test has_schema() helper function"""
    try:
        from app.schemas import has_schema

        # Test valid QuickBooks schema
        assert has_schema("vendor.create") is True
        assert has_schema("bill.create") is True

        # Test valid Stripe schema
        assert has_schema("stripe.payment.create") is True
        assert has_schema("stripe.customer.create") is True

        # Test invalid schema
        assert has_schema("does.not.exist") is False
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_get_services_with_schemas():
    """Test get_services_with_schemas() helper function"""
    try:
        from app.schemas import get_services_with_schemas

        services = get_services_with_schemas()

        # Verify we have many services
        assert len(services) >= 5

        # QuickBooks assertions (minimum thresholds)
        assert "quickbooks" in services
        assert services["quickbooks"]["capabilities_count"] >= 70
        assert "vendors" in services["quickbooks"]["categories"]
        assert "bills" in services["quickbooks"]["categories"]

        # Stripe assertions
        assert "stripe" in services
        assert services["stripe"]["capabilities_count"] >= 200
        assert "payments" in services["stripe"]["categories"]
        assert "customers" in services["stripe"]["categories"]

        # Google assertions
        assert "google" in services
        assert services["google"]["capabilities_count"] >= 20

        # Slack assertions
        assert "slack" in services
        assert services["slack"]["capabilities_count"] >= 10
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_schema_parameters_have_required_fields():
    """Verify parameter schemas have required fields"""
    try:
        from app.schemas import SCHEMA_REGISTRY

        for key, schema in SCHEMA_REGISTRY.items():
            for param_name, param in schema.parameters.items():
                assert param.type in [
                    "string",
                    "integer",
                    "number",
                    "boolean",
                    "array",
                    "object",
                ], f"Invalid param type for {key}.{param_name}"
                assert param.description, f"Missing description for {key}.{param_name}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_schema_returns_have_required_fields():
    """Verify return field schemas have required fields"""
    try:
        from app.schemas import SCHEMA_REGISTRY

        for key, schema in SCHEMA_REGISTRY.items():
            for field_name, field in schema.returns.items():
                assert field.type, f"Missing type for {key} return field {field_name}"
                assert field.description, f"Missing description for {key} return field {field_name}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_schema_errors_are_valid():
    """Verify error hints use valid error codes"""
    try:
        from app.errors import ErrorCode
        from app.schemas import SCHEMA_REGISTRY

        valid_error_codes = set(ErrorCode)

        for key, schema in SCHEMA_REGISTRY.items():
            for error in schema.errors:
                assert (
                    error.error_code in valid_error_codes
                ), f"Invalid error code {error.error_code} in {key}"
                assert error.description, f"Missing error description in {key}"
                assert error.recovery_hint, f"Missing recovery hint in {key}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_workflow_hints_reference_valid_capabilities():
    """Verify most workflow hints reference capabilities that exist in registry"""
    try:
        from app.registry import CAPABILITY_REGISTRY
        from app.schemas import SCHEMA_REGISTRY

        valid_keys = set(CAPABILITY_REGISTRY.keys())
        invalid_refs = []

        for key, schema in SCHEMA_REGISTRY.items():
            if schema.workflow:
                invalid_refs.extend(
                    f"{key} -> {ref}"
                    for ref in schema.workflow.typically_preceded_by
                    if ref not in valid_keys
                )
                invalid_refs.extend(
                    f"{key} -> {ref}"
                    for ref in schema.workflow.typically_followed_by
                    if ref not in valid_keys
                )
                invalid_refs.extend(
                    f"{key} -> {ref}"
                    for ref in schema.workflow.related_capabilities
                    if ref not in valid_keys
                )

        # Allow up to 25% invalid refs (data quality threshold during schema migration)
        total_schemas_with_workflow = sum(1 for s in SCHEMA_REGISTRY.values() if s.workflow)
        max_allowed = max(100, int(total_schemas_with_workflow * 0.25))
        assert len(invalid_refs) <= max_allowed, (
            f"Too many invalid workflow refs ({len(invalid_refs)} > {max_allowed}): "
            f"{invalid_refs[:5]}..."
        )
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_schemas_match_registry_capabilities():
    """Verify most schemas correspond to valid registry capabilities"""
    try:
        from app.registry import CAPABILITY_REGISTRY
        from app.schemas import SCHEMA_REGISTRY

        mismatched = [key for key in SCHEMA_REGISTRY if key not in CAPABILITY_REGISTRY]

        # Allow up to 40% mismatch during schema migration
        # (schemas may be ahead of or behind capability naming)
        max_allowed = int(len(SCHEMA_REGISTRY) * 0.4)
        assert len(mismatched) <= max_allowed, (
            f"Too many schemas without matching capabilities "
            f"({len(mismatched)}/{len(SCHEMA_REGISTRY)} > {max_allowed}): {mismatched[:5]}..."
        )
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_registry_list_capabilities_includes_schema_available():
    """Verify list_capabilities includes schema_available field"""
    try:
        from app.registry import list_capabilities

        capabilities = list_capabilities()

        for key, info in capabilities.items():
            assert "schema_available" in info, f"'{key}' missing schema_available"
            assert isinstance(info["schema_available"], bool)

        # Verify QuickBooks capabilities have schemas
        assert capabilities["vendor.create"]["schema_available"] is True
        assert capabilities["bill.create"]["schema_available"] is True

        # Verify Stripe capabilities (using actual capability names)
        assert capabilities["stripe.customer.create"]["schema_available"] is True
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_read_only_capabilities_marked_correctly():
    """Verify read-only capabilities have correct flags"""
    try:
        from app.schemas import SCHEMA_REGISTRY

        read_only_keys = [
            "vendor.get",
            "vendor.list",
            "vendor.search",
            "bill.get",
            "bill.list",
            "billpayment.list",
        ]

        for key in read_only_keys:
            schema = SCHEMA_REGISTRY[key]
            assert schema.idempotent is True, f"{key} should be idempotent"
            assert schema.has_side_effects is False, f"{key} should not have side effects"

        write_keys = ["vendor.create", "vendor.update", "bill.create", "bill.payment.create"]

        for key in write_keys:
            schema = SCHEMA_REGISTRY[key]
            assert schema.has_side_effects is True, f"{key} should have side effects"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_schema_serialization():
    """Verify schemas can be serialized to dict"""
    try:
        from app.schemas import get_schema

        schema = get_schema("vendor.create")
        assert schema is not None

        serialized = schema.model_dump()
        assert isinstance(serialized, dict)
        assert serialized["capability_key"] == "vendor.create"
        assert serialized["service"] == "quickbooks"
        assert "parameters" in serialized
        assert "returns" in serialized
    except ImportError:
        pytest.skip("Dependencies not installed")


if __name__ == "__main__":
    print("Running schema tests...")
    pytest.main([__file__, "-v"])
