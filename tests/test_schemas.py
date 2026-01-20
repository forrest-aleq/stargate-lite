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

        # 71 QuickBooks + 224 Stripe + 18 Gmail + 14 Slack + 18 HubSpot
        # + 11 Plaid + 5 Google Drive + 5 OneDrive + 5 Dropbox + 20 NetSuite = 391 total
        assert len(SCHEMA_REGISTRY) == 391, f"Expected 391 schemas, got {len(SCHEMA_REGISTRY)}"
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
        assert len(all_schemas) == 391

        # Test filtered by service
        qb_schemas = list_schemas(service="quickbooks")
        assert len(qb_schemas) == 71

        stripe_schemas = list_schemas(service="stripe")
        assert len(stripe_schemas) == 224

        # Google now includes Gmail (18) + Google Drive (5) = 23
        google_schemas = list_schemas(service="google")
        assert len(google_schemas) == 23

        slack_schemas = list_schemas(service="slack")
        assert len(slack_schemas) == 14

        hubspot_schemas = list_schemas(service="hubspot")
        assert len(hubspot_schemas) == 18

        # New services
        plaid_schemas = list_schemas(service="plaid")
        assert len(plaid_schemas) == 11

        microsoft_schemas = list_schemas(service="microsoft")
        assert len(microsoft_schemas) == 5

        dropbox_schemas = list_schemas(service="dropbox")
        assert len(dropbox_schemas) == 5

        netsuite_schemas = list_schemas(service="netsuite")
        assert len(netsuite_schemas) == 20

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

        # QuickBooks assertions
        assert "quickbooks" in services
        assert services["quickbooks"]["capabilities_count"] == 71
        assert "vendors" in services["quickbooks"]["categories"]
        assert "bills" in services["quickbooks"]["categories"]
        assert "invoices" in services["quickbooks"]["categories"]
        assert "customers" in services["quickbooks"]["categories"]
        assert "reports" in services["quickbooks"]["categories"]

        # Stripe assertions
        assert "stripe" in services
        assert services["stripe"]["capabilities_count"] == 224
        assert "payments" in services["stripe"]["categories"]
        assert "customers" in services["stripe"]["categories"]
        assert "subscriptions" in services["stripe"]["categories"]

        # Google assertions (Gmail + Drive)
        assert "google" in services
        assert services["google"]["capabilities_count"] == 23  # 18 Gmail + 5 Drive
        assert "email" in services["google"]["categories"]
        assert "files" in services["google"]["categories"]

        # Slack assertions
        assert "slack" in services
        assert services["slack"]["capabilities_count"] == 14
        assert "messaging" in services["slack"]["categories"]
        assert "channels" in services["slack"]["categories"]
        assert "users" in services["slack"]["categories"]
        assert "reactions" in services["slack"]["categories"]
        assert "search" in services["slack"]["categories"]

        # HubSpot assertions
        assert "hubspot" in services
        assert services["hubspot"]["capabilities_count"] == 18
        assert "contacts" in services["hubspot"]["categories"]
        assert "deals" in services["hubspot"]["categories"]
        assert "companies" in services["hubspot"]["categories"]

        # Plaid assertions
        assert "plaid" in services
        assert services["plaid"]["capabilities_count"] == 11
        assert "banking" in services["plaid"]["categories"]

        # Microsoft assertions (OneDrive)
        assert "microsoft" in services
        assert services["microsoft"]["capabilities_count"] == 5
        assert "files" in services["microsoft"]["categories"]

        # Dropbox assertions
        assert "dropbox" in services
        assert services["dropbox"]["capabilities_count"] == 5
        assert "files" in services["dropbox"]["categories"]

        # NetSuite assertions
        assert "netsuite" in services
        assert services["netsuite"]["capabilities_count"] == 20
        assert "accounting" in services["netsuite"]["categories"]
        assert "payables" in services["netsuite"]["categories"]
        assert "vendors" in services["netsuite"]["categories"]
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
    """Verify workflow hints reference capabilities that exist in registry"""
    try:
        from app.registry import CAPABILITY_REGISTRY
        from app.schemas import SCHEMA_REGISTRY

        valid_keys = set(CAPABILITY_REGISTRY.keys())

        for key, schema in SCHEMA_REGISTRY.items():
            if schema.workflow:
                for ref in schema.workflow.typically_preceded_by:
                    assert ref in valid_keys, f"Invalid workflow ref '{ref}' in {key}"
                for ref in schema.workflow.typically_followed_by:
                    assert ref in valid_keys, f"Invalid workflow ref '{ref}' in {key}"
                for ref in schema.workflow.related_capabilities:
                    assert ref in valid_keys, f"Invalid workflow ref '{ref}' in {key}"
    except ImportError:
        pytest.skip("Dependencies not installed")


def test_schemas_match_registry_capabilities():
    """Verify all schemas correspond to valid registry capabilities"""
    try:
        from app.registry import CAPABILITY_REGISTRY
        from app.schemas import SCHEMA_REGISTRY

        for key in SCHEMA_REGISTRY:
            assert (
                key in CAPABILITY_REGISTRY
            ), f"Schema '{key}' has no matching capability in registry"
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

        # Verify QuickBooks capabilities
        assert capabilities["vendor.create"]["schema_available"] is True
        assert capabilities["bill.create"]["schema_available"] is True

        # Verify Stripe capabilities
        assert capabilities["stripe.payment.create"]["schema_available"] is True
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
