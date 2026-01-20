"""
Brex connector for Stargate Lite
Handles corporate cards, expenses, payments
Uses Brex API (October 2025)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class BrexConnector:
    """Brex API connector for modern finance"""

    BASE_URL = "https://platform.brexapis.com"

    def __init__(self) -> None:
        self.client_id = os.getenv("BREX_CLIENT_ID")
        self.client_secret = os.getenv("BREX_CLIENT_SECRET")

    def _get_access_token(self, args: dict[str, Any]) -> str:
        """Extract and validate access_token from args."""
        access_token = args.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("access_token is required and must be a string")
        return access_token

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    def _make_request(
        self, method: str, endpoint: str, access_token: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(access_token)

        if method not in ["GET", "POST", "PUT"]:
            raise ValueError(f"Unsupported method: {method}")

        if method == "GET":
            return http_client.get(url=url, service="brex", headers=headers, params=data)
        else:
            # POST, PUT
            result: dict[str, Any] = http_client.request(
                method=method, url=url, service="brex", headers=headers, json=data
            )
            return result

    def list_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List card transactions"""
        access_token = self._get_access_token(args)
        params = {
            "posted_at_start": args.get("start_date"),
            "posted_at_end": args.get("end_date"),
            "limit": args.get("limit", 100),
        }

        result = self._make_request("GET", "/v2/transactions/card/primary", access_token, params)

        return {
            "transactions": [
                {
                    "id": t["id"],
                    "amount": t.get("amount", {}).get("amount"),
                    "merchant_name": t.get("merchant", {}).get("name"),
                    "card_id": t.get("card_id"),
                    "user_id": t.get("user_id"),
                    "status": t.get("status"),
                    "posted_at": t.get("posted_at"),
                }
                for t in result.get("items", [])
            ],
            "next_cursor": result.get("next_cursor"),
        }

    def list_expenses(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List expenses with categories and receipts"""
        access_token = self._get_access_token(args)
        params = {"limit": args.get("limit", 100)}

        result = self._make_request("GET", "/v1/expenses/card", access_token, params)

        return {
            "expenses": [
                {
                    "id": e["id"],
                    "amount": e.get("amount"),
                    "memo": e.get("memo"),
                    "category": e.get("category"),
                    "receipts": e.get("receipts", []),
                    "purchase_date": e.get("purchase_date"),
                }
                for e in result.get("items", [])
            ]
        }

    def create_virtual_card(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a virtual card with spending limits"""
        access_token = self._get_access_token(args)

        card_data = {
            "owner": {"user_id": args.get("user_id")},
            "display_name": args.get("display_name"),
            "spending_controls": {
                "spend_limit": args.get("spend_limit"),
                "spend_limit_duration": args.get("limit_duration", "MONTHLY"),
            },
        }

        result = self._make_request("POST", "/v2/cards", access_token, card_data)

        return {
            "card_id": result["id"],
            "last_four": result.get("last_four"),
            "status": result.get("status"),
        }

    def lock_card(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Lock a card"""
        access_token = self._get_access_token(args)
        card_id = args.get("card_id")

        self._make_request("POST", f"/v2/cards/{card_id}/lock", access_token, {})

        return {"card_id": card_id, "status": "locked"}

    def unlock_card(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Unlock a card"""
        access_token = self._get_access_token(args)
        card_id = args.get("card_id")

        self._make_request("POST", f"/v2/cards/{card_id}/unlock", access_token, {})

        return {"card_id": card_id, "status": "active"}

    def update_card_limit(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update card spending limit"""
        access_token = self._get_access_token(args)
        card_id = args.get("card_id")

        limit_data = {"spending_controls": {"spend_limit": args.get("new_limit")}}

        self._make_request("PUT", f"/v2/cards/{card_id}", access_token, limit_data)

        return {"card_id": card_id, "new_limit": args.get("new_limit"), "status": "updated"}

    def create_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create vendor payment"""
        access_token = self._get_access_token(args)

        payment_data = {
            "counterparty_id": args.get("counterparty_id"),
            "amount": {"amount": args.get("amount"), "currency": args.get("currency", "USD")},
            "description": args.get("description"),
        }

        result = self._make_request("POST", "/v1/payments", access_token, payment_data)

        return {
            "payment_id": result["id"],
            "status": result.get("status"),
            "amount": result.get("amount"),
        }

    def get_account_balance(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get cash account balance"""
        access_token = self._get_access_token(args)

        result = self._make_request("GET", "/v2/accounts/cash", access_token)

        return {
            "accounts": [
                {
                    "account_id": acc["id"],
                    "name": acc.get("name"),
                    "current_balance": acc.get("current_balance"),
                    "available_balance": acc.get("available_balance"),
                    "currency": acc.get("currency"),
                }
                for acc in result.get("accounts", [])
            ]
        }
