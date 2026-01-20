"""
Plaid connector for Stargate Lite
Handles banking data aggregation, transactions, auth, transfers
Uses Plaid API (October 2025) with latest features
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class PlaidConnector:
    """Plaid API connector for banking data"""

    SANDBOX_URL = "https://sandbox.plaid.com"
    DEVELOPMENT_URL = "https://development.plaid.com"
    PRODUCTION_URL = "https://production.plaid.com"

    def __init__(self) -> None:
        self.client_id = os.getenv("PLAID_CLIENT_ID")
        self.secret = os.getenv("PLAID_SECRET")
        self.environment = os.getenv("PLAID_ENVIRONMENT", "sandbox")

        # Set base URL based on environment
        if self.environment == "sandbox":
            self.base_url = self.SANDBOX_URL
        elif self.environment == "development":
            self.base_url = self.DEVELOPMENT_URL
        else:
            self.base_url = self.PRODUCTION_URL

    def _make_request(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Make authenticated request to Plaid API"""
        logger.debug(
            "Plaid API request", service="plaid", endpoint=endpoint, log_event="plaid_api_request"
        )

        # Add client credentials to every request
        data["client_id"] = self.client_id
        data["secret"] = self.secret

        url = f"{self.base_url}{endpoint}"

        return http_client.post(
            url=url, service="plaid", headers={"Content-Type": "application/json"}, json=data
        )

    def create_link_token(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a Link token for Plaid Link initialization"""
        logger.info(
            "Creating link token",
            service="plaid",
            products=args.get("products", ["transactions", "auth", "identity"]),
            log_event="plaid_link_token_create",
        )
        data = {
            "user": {"client_user_id": f"{org_id}:{user_id}"},
            "client_name": args.get("client_name", "Stargate Lite"),
            "products": args.get("products", ["transactions", "auth", "identity"]),
            "country_codes": ["US"],
            "language": "en",
        }

        if args.get("webhook"):
            data["webhook"] = args["webhook"]

        result = self._make_request("/link/token/create", data)

        logger.info("Link token created", service="plaid", log_event="plaid_link_token_created")

        return {"link_token": result["link_token"], "expiration": result["expiration"]}

    def exchange_public_token(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Exchange public token for access token"""
        logger.info("Exchanging public token", service="plaid", log_event="plaid_token_exchange")
        data = {"public_token": args.get("public_token")}

        result = self._make_request("/item/public_token/exchange", data)

        logger.info(
            "Token exchanged",
            service="plaid",
            item_id=result.get("item_id"),
            log_event="plaid_token_exchanged",
        )

        # Store access_token securely for this org/user
        # In production, this would go to CredentialManager
        return {"access_token": result["access_token"], "item_id": result["item_id"]}

    def get_transactions_sync(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get transactions using /transactions/sync (2025 recommended method)"""
        logger.info(
            "Syncing transactions",
            service="plaid",
            has_cursor=bool(args.get("cursor")),
            log_event="plaid_transactions_sync",
        )
        data = {"access_token": args.get("access_token")}

        if args.get("cursor"):
            data["cursor"] = args["cursor"]

        if args.get("count"):
            data["count"] = args["count"]

        result = self._make_request("/transactions/sync", data)

        logger.info(
            "Transactions synced",
            service="plaid",
            added_count=len(result.get("added", [])),
            modified_count=len(result.get("modified", [])),
            removed_count=len(result.get("removed", [])),
            log_event="plaid_transactions_synced",
        )

        return {
            "transactions_added": [
                {
                    "transaction_id": t["transaction_id"],
                    "account_id": t["account_id"],
                    "amount": t["amount"],
                    "date": t["date"],
                    "name": t["name"],
                    "merchant_name": t.get("merchant_name"),
                    "category": t.get("category", []),
                    "pending": t.get("pending", False),
                }
                for t in result.get("added", [])
            ],
            "transactions_modified": result.get("modified", []),
            "transactions_removed": [r["transaction_id"] for r in result.get("removed", [])],
            "next_cursor": result.get("next_cursor"),
            "has_more": result.get("has_more", False),
        }

    def get_auth(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get bank account numbers for ACH/wire transfers"""
        logger.info("Getting auth data", service="plaid", log_event="plaid_auth_get")
        data = {"access_token": args.get("access_token")}

        result = self._make_request("/auth/get", data)

        logger.info(
            "Auth data retrieved",
            service="plaid",
            account_count=len(result.get("accounts", [])),
            log_event="plaid_auth_retrieved",
        )

        return {
            "accounts": [
                {
                    "account_id": acc["account_id"],
                    "name": acc["name"],
                    "official_name": acc.get("official_name"),
                    "type": acc["type"],
                    "subtype": acc["subtype"],
                    "mask": acc.get("mask"),
                    "balance": acc["balances"],
                    # Routing/account numbers (may be tokenized at some banks)
                    "routing": (
                        acc["numbers"]["ach"][0]["routing"]
                        if acc.get("numbers", {}).get("ach")
                        else None
                    ),
                    "account": (
                        acc["numbers"]["ach"][0]["account"]
                        if acc.get("numbers", {}).get("ach")
                        else None
                    ),
                    "wire_routing": (
                        acc["numbers"]["ach"][0]["wire_routing"]
                        if acc.get("numbers", {}).get("ach")
                        else None
                    ),
                }
                for acc in result.get("accounts", [])
            ],
            "numbers": result.get("numbers", {}),
            "item_id": result.get("item", {}).get("item_id"),
        }

    def create_transfer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a transfer (2025 Transfer API)"""
        logger.info(
            "Creating transfer",
            service="plaid",
            transfer_type=args.get("transfer_type", "debit"),
            amount=args.get("amount"),
            network=args.get("network", "ach"),
            log_event="plaid_transfer_create",
        )
        data = {
            "access_token": args.get("access_token"),
            "account_id": args.get("account_id"),
            "type": args.get("transfer_type", "debit"),  # debit or credit
            "network": args.get("network", "ach"),  # ach or same-day-ach
            "amount": str(args.get("amount")),
            "description": args.get("description", "Transfer"),
            "ach_class": args.get("ach_class", "ppd"),  # ppd, ccd, web
            "user": {"legal_name": args.get("user_legal_name")},
        }

        if args.get("idempotency_key"):
            data["idempotency_key"] = args["idempotency_key"]

        result = self._make_request("/transfer/create", data)

        logger.info(
            "Transfer created",
            service="plaid",
            transfer_id=result["transfer"]["id"],
            status=result["transfer"]["status"],
            log_event="plaid_transfer_created",
        )

        return {
            "transfer_id": result["transfer"]["id"],
            "status": result["transfer"]["status"],
            "amount": result["transfer"]["amount"],
            "network": result["transfer"]["network"],
            "expected_funds_available_date": result["transfer"].get(
                "expected_funds_available_date"
            ),
        }

    def get_transfer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get transfer status"""
        logger.info(
            "Getting transfer status",
            service="plaid",
            transfer_id=args.get("transfer_id"),
            log_event="plaid_transfer_get",
        )
        data = {"transfer_id": args.get("transfer_id")}

        result = self._make_request("/transfer/get", data)

        return {
            "transfer_id": result["transfer"]["id"],
            "status": result["transfer"]["status"],
            "amount": result["transfer"]["amount"],
            "type": result["transfer"]["type"],
            "created": result["transfer"]["created"],
            "network": result["transfer"]["network"],
            "cancellable": result["transfer"]["cancellable"],
        }

    def get_identity(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get identity information for account owner"""
        logger.info("Getting identity data", service="plaid", log_event="plaid_identity_get")
        data = {"access_token": args.get("access_token")}

        result = self._make_request("/identity/get", data)

        logger.info(
            "Identity data retrieved",
            service="plaid",
            account_count=len(result.get("accounts", [])),
            log_event="plaid_identity_retrieved",
        )

        return {
            "accounts": [
                {
                    "account_id": acc["account_id"],
                    "owners": [
                        {
                            "names": owner.get("names", []),
                            "phone_numbers": owner.get("phone_numbers", []),
                            "emails": owner.get("emails", []),
                            "addresses": owner.get("addresses", []),
                        }
                        for owner in acc.get("owners", [])
                    ],
                }
                for acc in result.get("accounts", [])
            ]
        }

    def get_balance(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get real-time balance for accounts"""
        logger.info(
            "Getting account balances",
            service="plaid",
            account_count=len(args.get("account_ids", [])) or "all",
            log_event="plaid_balance_get",
        )
        data = {"access_token": args.get("access_token")}

        if args.get("account_ids"):
            data["options"] = {"account_ids": args["account_ids"]}

        result = self._make_request("/accounts/balance/get", data)

        logger.info(
            "Balances retrieved",
            service="plaid",
            account_count=len(result.get("accounts", [])),
            log_event="plaid_balance_retrieved",
        )

        return {
            "accounts": [
                {
                    "account_id": acc["account_id"],
                    "name": acc["name"],
                    "type": acc["type"],
                    "subtype": acc["subtype"],
                    "current_balance": acc["balances"]["current"],
                    "available_balance": acc["balances"].get("available"),
                    "limit": acc["balances"].get("limit"),
                    "currency": acc["balances"].get("iso_currency_code", "USD"),
                }
                for acc in result.get("accounts", [])
            ]
        }

    def get_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get list of accounts"""
        logger.info("Getting accounts", service="plaid", log_event="plaid_accounts_get")
        data = {"access_token": args.get("access_token")}

        result = self._make_request("/accounts/get", data)

        logger.info(
            "Accounts retrieved",
            service="plaid",
            account_count=len(result.get("accounts", [])),
            log_event="plaid_accounts_retrieved",
        )

        return {
            "accounts": [
                {
                    "account_id": acc["account_id"],
                    "name": acc["name"],
                    "official_name": acc.get("official_name"),
                    "type": acc["type"],
                    "subtype": acc["subtype"],
                    "mask": acc.get("mask"),
                }
                for acc in result.get("accounts", [])
            ],
            "item_id": result.get("item", {}).get("item_id"),
        }

    def create_processor_token(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create processor token for payment processors"""
        logger.info(
            "Creating processor token",
            service="plaid",
            processor=args.get("processor", "stripe"),
            log_event="plaid_processor_token_create",
        )
        data = {
            "access_token": args.get("access_token"),
            "account_id": args.get("account_id"),
            "processor": args.get("processor", "stripe"),  # stripe, dwolla, etc.
        }

        result = self._make_request("/processor/token/create", data)

        logger.info(
            "Processor token created",
            service="plaid",
            processor=args.get("processor", "stripe"),
            log_event="plaid_processor_token_created",
        )

        return {"processor_token": result["processor_token"]}
