"""
Mercury connector for Stargate Lite
Handles business banking, payments, transfers
Uses Mercury API (October 2025)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class MercuryConnector:
    """Mercury API connector for startup banking"""

    BASE_URL = "https://api.mercury.com/api/v1"

    def __init__(self) -> None:
        self.api_key = os.getenv("MERCURY_API_KEY")

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()

        if method not in ["GET", "POST"]:
            raise ValueError(f"Unsupported method: {method}")

        if method == "GET":
            return http_client.get(url=url, service="mercury", headers=headers, params=data)
        else:
            # POST
            return http_client.post(url=url, service="mercury", headers=headers, json=data)

    def list_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all Mercury accounts"""
        result = self._make_request("GET", "/accounts")

        return {
            "accounts": [
                {
                    "account_id": acc["id"],
                    "name": acc.get("name"),
                    "type": acc.get("type"),
                    "balance": acc.get("balance"),
                    "currency": acc.get("currency", "USD"),
                    "status": acc.get("status"),
                }
                for acc in result.get("accounts", [])
            ]
        }

    def get_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get transactions for an account"""
        params = {
            "account_id": args.get("account_id"),
            "start": args.get("start_date"),
            "end": args.get("end_date"),
            "limit": args.get("limit", 100),
            "offset": args.get("offset", 0),
        }

        result = self._make_request("GET", "/transactions", params)

        return {
            "transactions": [
                {
                    "transaction_id": t["id"],
                    "amount": t.get("amount"),
                    "description": t.get("description"),
                    "status": t.get("status"),
                    "posted_at": t.get("postedAt"),
                    "counterparty_name": t.get("counterpartyName"),
                }
                for t in result.get("transactions", [])
            ],
            "total": result.get("total"),
        }

    def create_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create ACH payment (100 free per month)"""
        payment_data = {
            "account_id": args.get("account_id"),
            "recipient_id": args.get("recipient_id"),
            "amount": args.get("amount"),
            "description": args.get("description", "Payment via Stargate"),
            "idempotency_key": args.get("idempotency_key"),
        }

        result = self._make_request("POST", "/payments", payment_data)

        return {
            "payment_id": result["id"],
            "status": result.get("status"),
            "amount": result.get("amount"),
            "estimated_delivery": result.get("estimatedDelivery"),
        }

    def create_recipient(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a payment recipient"""
        recipient_data = {
            "name": args.get("name"),
            "email": args.get("email"),
            "routing_number": args.get("routing_number"),
            "account_number": args.get("account_number"),
            "account_type": args.get("account_type", "checking"),
        }

        result = self._make_request("POST", "/recipients", recipient_data)

        return {
            "recipient_id": result["id"],
            "name": result.get("name"),
            "status": result.get("status"),
        }

    def list_recipients(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payment recipients"""
        result = self._make_request("GET", "/recipients")

        return {
            "recipients": [
                {
                    "recipient_id": r["id"],
                    "name": r.get("name"),
                    "email": r.get("email"),
                    "status": r.get("status"),
                }
                for r in result.get("recipients", [])
            ]
        }

    def create_wire(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create wire transfer (domestic or international)"""
        wire_data = {
            "account_id": args.get("account_id"),
            "recipient_id": args.get("recipient_id"),
            "amount": args.get("amount"),
            "type": args.get("wire_type", "domestic"),  # domestic or international
            "description": args.get("description"),
        }

        result = self._make_request("POST", "/wires", wire_data)

        return {
            "wire_id": result["id"],
            "status": result.get("status"),
            "amount": result.get("amount"),
            "fee": result.get("fee", 0),  # Free for Mercury
        }
