"""
Ramp connector for Stargate Lite
Handles corporate cards, expenses, reimbursements
Uses Ramp API (October 2025)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class RampConnector:
    """Ramp API connector for corporate card management"""

    BASE_URL = "https://api.ramp.com/developer/v1"

    def __init__(self) -> None:
        self.client_id = os.getenv("RAMP_CLIENT_ID")
        self.client_secret = os.getenv("RAMP_CLIENT_SECRET")

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

        if method not in ["GET", "POST", "PATCH"]:
            raise ValueError(f"Unsupported method: {method}")

        if method == "GET":
            return http_client.get(url=url, service="ramp", headers=headers, params=data)
        else:
            # POST, PATCH
            result: dict[str, Any] = http_client.request(
                method=method, url=url, service="ramp", headers=headers, json=data
            )
            return result

    def list_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List card transactions"""
        access_token = self._get_access_token(args)
        params = {
            "start": args.get("start_date"),
            "end": args.get("end_date"),
            "page_size": args.get("page_size", 50),
        }

        result = self._make_request("GET", "/transactions", access_token, params)

        return {
            "transactions": [
                {
                    "id": t["id"],
                    "amount": t["amount"],
                    "merchant_name": t.get("merchant_name"),
                    "card_id": t.get("card_id"),
                    "user_id": t.get("user_id"),
                    "state": t["state"],
                    "created_at": t["created_at"],
                }
                for t in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def create_card(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a virtual or physical card"""
        access_token = self._get_access_token(args)

        card_data = {
            "user_id": args.get("ramp_user_id"),
            "display_name": args.get("display_name"),
            "spending_restrictions": args.get("spending_restrictions", {}),
            "is_physical": args.get("is_physical", False),
        }

        result = self._make_request("POST", "/cards", access_token, card_data)

        return {
            "card_id": result["id"],
            "last_four": result.get("last_four"),
            "state": result["state"],
            "is_physical": result.get("is_physical"),
        }

    def create_reimbursement(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create an expense reimbursement"""
        access_token = self._get_access_token(args)

        reimbursement_data = {
            "user_id": args.get("ramp_user_id"),
            "amount": args.get("amount"),
            "merchant_name": args.get("merchant_name"),
            "transaction_date": args.get("transaction_date"),
            "receipts": args.get("receipts", []),
        }

        result = self._make_request("POST", "/reimbursements", access_token, reimbursement_data)

        return {
            "reimbursement_id": result["id"],
            "amount": result["amount"],
            "status": result["status"],
        }

    def get_users(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List Ramp users"""
        access_token = self._get_access_token(args)

        result = self._make_request("GET", "/users", access_token)

        return {
            "users": [
                {
                    "id": u["id"],
                    "email": u.get("email"),
                    "first_name": u.get("first_name"),
                    "last_name": u.get("last_name"),
                    "role": u.get("role"),
                }
                for u in result.get("data", [])
            ]
        }
