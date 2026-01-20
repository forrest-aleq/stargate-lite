#!/usr/bin/env python3
"""
Setup test credentials for MARS E2E testing
Based on MARS team specifications
"""

from datetime import datetime, timedelta

from app.database import CredentialManager, init_db

print("=" * 60)
print("MARS E2E Testing - Database Setup")
print("=" * 60)

# Initialize database
print("\n1. Initializing database...")
init_db()
print("✅ Database initialized")

# Scenario 1: Happy path - Customer QuickBooks credential
print("\n2. Setting up Scenario 1: happy_path_vendor_onboarding_customer_creds")
try:
    CredentialManager.store_credential(
        org_id="mars_test_org",
        user_id="mars_test_user",
        service="quickbooks",
        access_token="mock_quickbooks_customer_token_valid",
        refresh_token="mock_quickbooks_refresh_token",
        credential_type="customer",
        token_expiry=datetime.utcnow() + timedelta(days=30),
        realm_id="mock_realm_12345",
        extra_data={"company_name": "Test Company", "environment": "sandbox"},
        created_by="mars_setup_script",
    )
    print("✅ Stored customer:quickbooks credential for mars_test_org/mars_test_user")
except Exception as e:
    print(f"❌ Failed to store QuickBooks credential: {e}")

# Scenario 3: Agent Gmail credential (ALEQ_SYSTEM)
print("\n3. Setting up Scenario 3: agent_credentials_only")
try:
    CredentialManager.store_credential(
        org_id="ALEQ_SYSTEM",
        user_id="ALEQ_AGENT",
        service="google",
        access_token="mock_gmail_agent_token_valid",
        refresh_token="mock_gmail_refresh_token",
        credential_type="agent",
        access_pattern="programmatic",
        token_expiry=datetime.utcnow() + timedelta(days=30),
        extra_data={"email": "aleq@aleq.ai"},
        created_by="mars_setup_script",
    )
    print("✅ Stored agent:google credential for ALEQ_SYSTEM/ALEQ_AGENT")
except Exception as e:
    print(f"❌ Failed to store Google credential: {e}")

# Scenario 2: Missing QuickBooks credential (DON'T store anything)
print("\n4. Setting up Scenario 2: missing_quickbooks_customer_credential")
print("✅ No credentials stored for mars_no_quickbooks (intentional for CREDENTIAL_MISSING test)")

# Scenario 4: No credentials needed (OCR)
print("\n5. Setting up Scenario 4: no_credentials_needed_ocr")
print("✅ No credentials needed - OCR capabilities don't require OAuth")

# Verification
print("\n" + "=" * 60)
print("VERIFICATION - Checking stored credentials")
print("=" * 60)

# Verify QuickBooks customer credential
print("\n1. Verifying customer:quickbooks for mars_test_org/mars_test_user")
quickbooks_cred = CredentialManager.get_credential(
    org_id="mars_test_org",
    user_id="mars_test_user",
    service="quickbooks",
    credential_type="customer",
)
if quickbooks_cred:
    print("✅ Found credential")
    print(f"   - credential_type: {quickbooks_cred['credential_type']}")
    print(f"   - token_expiry: {quickbooks_cred['token_expiry']}")
    print(f"   - realm_id: {quickbooks_cred['realm_id']}")
    print(f"   - access_pattern: {quickbooks_cred['access_pattern']}")
else:
    print("❌ Credential not found!")

# Verify Gmail agent credential
print("\n2. Verifying agent:google for ALEQ_SYSTEM/ALEQ_AGENT")
gmail_cred = CredentialManager.get_credential(
    org_id="ALEQ_SYSTEM", user_id="ALEQ_AGENT", service="google", credential_type="agent"
)
if gmail_cred:
    print("✅ Found credential")
    print(f"   - credential_type: {gmail_cred['credential_type']}")
    print(f"   - access_pattern: {gmail_cred['access_pattern']}")
    print(f"   - token_expiry: {gmail_cred['token_expiry']}")
else:
    print("❌ Credential not found!")

# Verify missing credential scenario
print("\n3. Verifying mars_no_quickbooks has NO credentials (CREDENTIAL_MISSING test)")
missing_cred = CredentialManager.get_credential(
    org_id="mars_no_quickbooks",
    user_id="mars_test_user",
    service="quickbooks",
    credential_type="customer",
)
if missing_cred is None:
    print("✅ No credential found (as expected)")
else:
    print("❌ Unexpected credential found!")

# Test get_credential_for_capability
print("\n" + "=" * 60)
print("TESTING get_credential_for_capability()")
print("=" * 60)

print("\n1. Testing vendor.create (QuickBooks) for mars_test_org/mars_test_user")
cred = CredentialManager.get_credential_for_capability(
    capability_key="vendor.create",
    org_id="mars_test_org",
    user_id="mars_test_user",
    use_delegation=False,
)
if cred and cred["credential_type"] == "customer":
    print("✅ Correctly retrieved customer credential")
else:
    print(f"❌ Unexpected result: {cred}")

print("\n2. Testing email.send for ALEQ_SYSTEM/ALEQ_AGENT")
cred = CredentialManager.get_credential_for_capability(
    capability_key="email.send", org_id="ALEQ_SYSTEM", user_id="ALEQ_AGENT", use_delegation=False
)
if cred and cred["credential_type"] == "agent":
    print("✅ Correctly retrieved agent credential")
else:
    print(f"❌ Unexpected result: {cred}")

print("\n3. Testing vendor.create for mars_no_quickbooks (should be None)")
cred = CredentialManager.get_credential_for_capability(
    capability_key="vendor.create",
    org_id="mars_no_quickbooks",
    user_id="mars_test_user",
    use_delegation=False,
)
if cred is None:
    print("✅ Correctly returned None (no credential)")
else:
    print(f"❌ Unexpected credential found: {cred}")

print("\n4. Testing ocr.text.extract (no credentials needed)")
cred = CredentialManager.get_credential_for_capability(
    capability_key="ocr.text.extract",
    org_id="mars_test_org",
    user_id="mars_test_user",
    use_delegation=False,
)
if cred is None:
    print("✅ Correctly returned None (no OAuth required)")
else:
    print(f"❌ Unexpected credential: {cred}")

# Summary
print("\n" + "=" * 60)
print("SETUP COMPLETE - READY FOR MARS E2E TESTING")
print("=" * 60)
print("\nTest Scenarios Ready:")
print("✅ Scenario 1: happy_path_vendor_onboarding_customer_creds")
print("   - org_id: mars_test_org")
print("   - user_id: mars_test_user")
print("   - Credentials: customer:quickbooks + agent:google")
print()
print("✅ Scenario 2: missing_quickbooks_customer_credential")
print("   - org_id: mars_no_quickbooks")
print("   - user_id: mars_test_user")
print("   - Credentials: NONE (expects CREDENTIAL_MISSING)")
print()
print("✅ Scenario 3: agent_credentials_only")
print("   - org_id: ALEQ_SYSTEM")
print("   - user_id: ALEQ_AGENT")
print("   - Credentials: agent:google")
print()
print("✅ Scenario 4: no_credentials_needed_ocr")
print("   - Any org_id/user_id")
print("   - Credentials: NONE (OCR doesn't need OAuth)")
print()
print("🚀 Stargate is ready for MARS E2E testing (QuickBooks Edition)!")
