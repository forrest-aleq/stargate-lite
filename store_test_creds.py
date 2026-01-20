"""
Store test credentials for MARS integration testing
"""

from datetime import datetime, timedelta

from app.database import CredentialManager

# Store test QuickBooks credentials
CredentialManager.store_credential(
    org_id="mars_test_org",
    user_id="mars_test_user",
    service="quickbooks",
    access_token="test_access_token_for_sandbox",
    refresh_token="test_refresh_token_for_sandbox",
    token_expiry=datetime.utcnow() + timedelta(days=30),  # Valid for 30 days
    realm_id="9130356189371859",  # Test realm ID
)

print("✅ Test credentials stored!")
print("org_id: mars_test_org")
print("user_id: mars_test_user")
print("service: quickbooks")
