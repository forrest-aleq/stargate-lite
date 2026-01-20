#!/usr/bin/env python3
"""
Sample script to add test credentials to Stargate Lite
Use this to manually add OAuth credentials after completing OAuth flows
"""

from datetime import datetime, timedelta

from app.database import CredentialManager, init_db


def add_quickbooks_credentials():
    """Add QuickBooks test credentials"""
    print("\n📝 Adding QuickBooks credentials...")

    org_id = input("Enter org_id: ")
    user_id = input("Enter user_id: ")
    access_token = input("Enter access_token: ")
    refresh_token = input("Enter refresh_token: ")
    realm_id = input("Enter realm_id (Company ID): ")

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="quickbooks",
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=datetime.utcnow() + timedelta(hours=1),
        realm_id=realm_id,
    )

    print("✅ QuickBooks credentials stored!")


def add_hubspot_credentials():
    """Add HubSpot test credentials"""
    print("\n📝 Adding HubSpot credentials...")

    org_id = input("Enter org_id: ")
    user_id = input("Enter user_id: ")
    access_token = input("Enter access_token: ")
    refresh_token = input("Enter refresh_token: ")

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="hubspot",
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=datetime.utcnow() + timedelta(hours=6),
    )

    print("✅ HubSpot credentials stored!")


def add_google_credentials():
    """Add Google/Gmail test credentials"""
    print("\n📝 Adding Google credentials...")

    org_id = input("Enter org_id: ")
    user_id = input("Enter user_id: ")
    access_token = input("Enter access_token: ")
    refresh_token = input("Enter refresh_token: ")

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="google",
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=datetime.utcnow() + timedelta(hours=1),
    )

    print("✅ Google credentials stored!")


def add_slack_credentials():
    """Add Slack test credentials"""
    print("\n📝 Adding Slack credentials...")

    org_id = input("Enter org_id: ")
    user_id = input("Enter user_id: ")
    access_token = input("Enter Bot User OAuth Token (starts with xoxb-): ")

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="slack",
        access_token=access_token,
        refresh_token=None,  # Slack tokens don't expire
    )

    print("✅ Slack credentials stored!")


def main():
    print("=" * 60)
    print("Stargate Lite - Credential Setup")
    print("=" * 60)

    # Initialize database
    init_db()

    while True:
        print("\n\nWhich service credentials do you want to add?")
        print("1. QuickBooks")
        print("2. HubSpot")
        print("3. Google/Gmail")
        print("4. Slack")
        print("5. Exit")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == "1":
            add_quickbooks_credentials()
        elif choice == "2":
            add_hubspot_credentials()
        elif choice == "3":
            add_google_credentials()
        elif choice == "4":
            add_slack_credentials()
        elif choice == "5":
            print("\n👋 Done!")
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
