#!/usr/bin/env python3
"""
Test script for dual credential system
Tests backward compatibility and new credential_type features
"""

import sys
from datetime import datetime, timedelta

# Test imports
try:
    from app.database import CredentialManager, init_db
    from app.registry import get_capability

    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Initialize database
try:
    init_db()
    print("✅ Database initialized")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    sys.exit(1)

# Test 1: Backward compatibility - store credential without credential_type
print("\n=== Test 1: Backward Compatibility ===")
try:
    CredentialManager.store_credential(
        org_id="test_org",
        user_id="test_user",
        service="quickbooks",
        access_token="test_token_123",
        refresh_token="refresh_token_123",
        token_expiry=datetime.utcnow() + timedelta(hours=1),
    )
    print("✅ Store credential without credential_type (defaults to customer)")

    # Retrieve without credential_type
    cred = CredentialManager.get_credential(
        org_id="test_org", user_id="test_user", service="quickbooks"
    )
    assert cred is not None
    assert cred["credential_type"] == "customer"
    print("✅ Retrieved credential defaults to customer type")
except Exception as e:
    print(f"❌ Test 1 failed: {e}")
    sys.exit(1)

# Test 2: Store and retrieve agent credential
print("\n=== Test 2: Agent Credentials ===")
try:
    CredentialManager.store_credential(
        org_id="ALEQ_SYSTEM",
        user_id="ALEQ_AGENT",
        service="google",
        access_token="agent_token_456",
        refresh_token="agent_refresh_456",
        token_expiry=datetime.utcnow() + timedelta(hours=1),
        credential_type="agent",
        access_pattern="programmatic",
    )
    print("✅ Stored agent credential with programmatic access")

    cred = CredentialManager.get_credential(
        org_id="ALEQ_SYSTEM", user_id="ALEQ_AGENT", service="google", credential_type="agent"
    )
    assert cred is not None
    assert cred["credential_type"] == "agent"
    assert cred["access_pattern"] == "programmatic"
    print("✅ Retrieved agent credential successfully")
except Exception as e:
    print(f"❌ Test 2 failed: {e}")
    sys.exit(1)

# Test 3: Store and retrieve delegated agent credential
print("\n=== Test 3: Delegated Agent Credentials ===")
try:
    CredentialManager.store_credential(
        org_id="customer_org",
        user_id="ALEQ_AGENT",
        service="google",
        access_token="delegated_token_789",
        refresh_token="delegated_refresh_789",
        token_expiry=datetime.utcnow() + timedelta(hours=1),
        credential_type="agent",
        access_pattern="delegate",
        created_by="customer_admin",
    )
    print("✅ Stored delegated agent credential")

    cred = CredentialManager.get_credential(
        org_id="customer_org", user_id="ALEQ_AGENT", service="google", credential_type="agent"
    )
    assert cred is not None
    assert cred["credential_type"] == "agent"
    assert cred["access_pattern"] == "delegate"
    print("✅ Retrieved delegated agent credential successfully")
except Exception as e:
    print(f"❌ Test 3 failed: {e}")
    sys.exit(1)

# Test 4: get_credential_for_capability - customer credential
print("\n=== Test 4: get_credential_for_capability (customer) ===")
try:
    # Store a customer credential
    CredentialManager.store_credential(
        org_id="test_org",
        user_id="test_user",
        service="quickbooks",
        access_token="customer_qb_token",
        credential_type="customer",
    )

    # Test get_credential_for_capability
    cred = CredentialManager.get_credential_for_capability(
        capability_key="vendor.create", org_id="test_org", user_id="test_user", use_delegation=False
    )
    assert cred is not None
    assert cred["credential_type"] == "customer"
    print("✅ get_credential_for_capability works for customer credentials")
except Exception as e:
    print(f"❌ Test 4 failed: {e}")
    sys.exit(1)

# Test 5: get_credential_for_capability - agent credential with fallback
print("\n=== Test 5: get_credential_for_capability (agent with fallback) ===")
try:
    # Store system agent credential for Google
    CredentialManager.store_credential(
        org_id="ALEQ_SYSTEM",
        user_id="ALEQ_AGENT",
        service="google",
        access_token="system_gmail_token",
        credential_type="agent",
        access_pattern="programmatic",
    )

    # Test get_credential_for_capability for Gmail (agent credential)
    cred = CredentialManager.get_credential_for_capability(
        capability_key="email.send", org_id="test_org", user_id="test_user", use_delegation=False
    )
    assert cred is not None
    assert cred["credential_type"] == "agent"
    assert cred["access_pattern"] == "programmatic"
    print("✅ get_credential_for_capability falls back to ALEQ_SYSTEM for agent credentials")
except Exception as e:
    print(f"❌ Test 5 failed: {e}")
    sys.exit(1)

# Test 6: Verify registry capabilities have credential_type
print("\n=== Test 6: Registry Capabilities ===")
try:
    # Check customer credential capability
    qb_vendor = get_capability("vendor.create")
    assert qb_vendor is not None
    assert qb_vendor.get("credential_type") == "customer"
    assert not qb_vendor.get("supports_delegation")
    print("✅ QuickBooks vendor.create has credential_type=customer")

    # Check agent credential capability
    gmail_send = get_capability("email.send")
    assert gmail_send is not None
    assert gmail_send.get("credential_type") == "agent"
    assert gmail_send.get("supports_delegation")
    assert "delegation_instructions" in gmail_send
    print("✅ Gmail email.send has credential_type=agent with delegation support")

    # Check OCR (no credentials)
    ocr = get_capability("ocr.text.extract")
    assert ocr is not None
    assert ocr.get("credential_type") is None
    assert not ocr.get("supports_delegation")
    print("✅ OCR has credential_type=None")
except Exception as e:
    print(f"❌ Test 6 failed: {e}")
    sys.exit(1)

# Test 7: Delete credential with credential_type
print("\n=== Test 7: Delete Credentials ===")
try:
    # Delete customer credential
    success = CredentialManager.delete_credential(
        org_id="test_org", user_id="test_user", service="quickbooks", credential_type="customer"
    )
    assert success
    print("✅ Deleted customer credential")

    # Verify it's gone
    cred = CredentialManager.get_credential(
        org_id="test_org", user_id="test_user", service="quickbooks", credential_type="customer"
    )
    assert cred is None
    print("✅ Verified credential deletion")
except Exception as e:
    print(f"❌ Test 7 failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Dual Credential System Working!")
print("=" * 60)
print("\nSummary:")
print("- Backward compatibility: ✅")
print("- Agent credentials: ✅")
print("- Delegated credentials: ✅")
print("- get_credential_for_capability: ✅")
print("- Registry credential_type: ✅")
print("- Credential deletion: ✅")
