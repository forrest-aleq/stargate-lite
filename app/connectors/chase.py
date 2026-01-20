"""
Chase Banking connector for Stargate Lite
Handles business banking, payments, ACH, wire transfers
Uses JPMorgan Chase Global Payments API (October 2025)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class ChaseConnector:
    """Chase/JPMorgan API connector for business banking"""

    # JPMorgan Chase Global Payments API base URL
    BASE_URL = "https://api.jpmorganpayments.com/tsapi/v1"

    def __init__(self) -> None:
        self.client_id = os.getenv("CHASE_CLIENT_ID")
        self.client_secret = os.getenv("CHASE_CLIENT_SECRET")

    def _get_access_token(self, args: dict[str, Any]) -> str:
        """Extract and validate access_token from args."""
        access_token = args.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("access_token is required and must be a string")
        return access_token

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, access_token: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(access_token)

        if method not in ["GET", "POST"]:
            raise ValueError(f"Unsupported method: {method}")

        if method == "GET":
            return http_client.get(url=url, service="chase", headers=headers, params=data)
        else:
            # POST - Chase may return 202 with paymentId/endToEndId in response body
            result: dict[str, Any] = http_client.request(
                method=method, url=url, service="chase", headers=headers, json=data
            )
            return result

    def list_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all business banking accounts"""
        access_token = self._get_access_token(args)

        result = self._make_request("GET", "/accounts", access_token)

        return {
            "accounts": [
                {
                    "account_id": acc["accountId"],
                    "account_number": acc.get("accountNumber"),
                    "account_type": acc.get("accountType"),
                    "currency": acc.get("currency", "USD"),
                    "status": acc.get("status"),
                    "nickname": acc.get("nickname"),
                }
                for acc in result.get("accounts", [])
            ]
        }

    def get_account_balance(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get account balance"""
        access_token = self._get_access_token(args)
        account_id = args.get("account_id")

        result = self._make_request("GET", f"/accounts/{account_id}/balance", access_token)

        return {
            "account_id": account_id,
            "current_balance": result.get("currentBalance"),
            "available_balance": result.get("availableBalance"),
            "currency": result.get("currency", "USD"),
            "as_of_date": result.get("asOfDate"),
        }

    def get_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get account transactions"""
        access_token = self._get_access_token(args)
        account_id = args.get("account_id")

        params = {
            "fromDate": args.get("from_date"),
            "toDate": args.get("to_date"),
            "limit": args.get("limit", 100),
            "offset": args.get("offset", 0),
        }

        result = self._make_request(
            "GET", f"/accounts/{account_id}/transactions", access_token, params
        )

        return {
            "transactions": [
                {
                    "transaction_id": t["transactionId"],
                    "amount": t.get("amount"),
                    "description": t.get("description"),
                    "type": t.get("type"),
                    "status": t.get("status"),
                    "posted_date": t.get("postedDate"),
                    "counterparty_name": t.get("counterpartyName"),
                }
                for t in result.get("transactions", [])
            ],
            "total_count": result.get("totalCount"),
        }

    def create_ach_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create ACH payment (free for Chase Business customers)"""
        access_token = self._get_access_token(args)

        payment_data = {
            "paymentMethod": "ACH",
            "sourceAccount": args.get("source_account_id"),
            "amount": {"value": args.get("amount"), "currency": args.get("currency", "USD")},
            "beneficiary": {
                "name": args.get("beneficiary_name"),
                "accountNumber": args.get("beneficiary_account"),
                "routingNumber": args.get("beneficiary_routing"),
                # checking or savings
                "accountType": args.get("beneficiary_account_type", "checking"),
            },
            "paymentDetails": {
                "description": args.get("description", "Payment via Stargate"),
                "reference": args.get("reference"),
            },
            # For future-dated payments
            "executionDate": args.get("execution_date"),
            # STANDARD, SAME_DAY, or REAL_TIME
            "speed": args.get("speed", "STANDARD"),
        }

        # Optional idempotency key (Global Payments 2)
        if args.get("idempotency_key"):
            payment_data["idempotencyKey"] = args["idempotency_key"]

        result = self._make_request("POST", "/payments", access_token, payment_data)

        return {
            "payment_id": result.get("paymentId"),
            "status": result.get("status"),
            "amount": result.get("amount"),
            "execution_date": result.get("executionDate"),
            "tracking_id": result.get("trackingId"),
        }

    def create_wire_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create domestic or international wire transfer"""
        access_token = self._get_access_token(args)

        wire_data = {
            "paymentMethod": "WIRE",
            "sourceAccount": args.get("source_account_id"),
            "amount": {"value": args.get("amount"), "currency": args.get("currency", "USD")},
            "beneficiary": {
                "name": args.get("beneficiary_name"),
                "accountNumber": args.get("beneficiary_account"),
                "routingNumber": args.get("beneficiary_routing"),
                "bankName": args.get("bank_name"),
                "bankAddress": args.get("bank_address"),
            },
            "paymentDetails": {
                "description": args.get("description"),
                "reference": args.get("reference"),
            },
            # DOMESTIC or INTERNATIONAL
            "wireType": args.get("wire_type", "DOMESTIC"),
            "executionDate": args.get("execution_date"),
        }

        # International wire additional fields
        if args.get("wire_type") == "INTERNATIONAL":
            wire_data["beneficiary"]["swiftCode"] = args.get("swift_code")
            wire_data["beneficiary"]["iban"] = args.get("iban")

        result = self._make_request("POST", "/payments", access_token, wire_data)

        return {
            "payment_id": result.get("paymentId"),
            "status": result.get("status"),
            "amount": result.get("amount"),
            "wire_reference": result.get("wireReference"),
            "estimated_delivery": result.get("estimatedDelivery"),
        }

    def get_payment_status(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get payment status and details"""
        access_token = self._get_access_token(args)
        payment_id = args.get("payment_id")

        result = self._make_request("GET", f"/payments/{payment_id}", access_token)

        return {
            "payment_id": result.get("paymentId"),
            "status": result.get("status"),
            "payment_method": result.get("paymentMethod"),
            "amount": result.get("amount"),
            "beneficiary": result.get("beneficiary"),
            "execution_date": result.get("executionDate"),
            "completion_date": result.get("completionDate"),
            "tracking_id": result.get("trackingId"),
            "error_details": result.get("errorDetails"),
        }

    def list_payments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payment history"""
        access_token = self._get_access_token(args)

        params = {
            "fromDate": args.get("from_date"),
            "toDate": args.get("to_date"),
            "status": args.get("status"),  # PENDING, COMPLETED, FAILED, etc.
            "paymentMethod": args.get("payment_method"),  # ACH, WIRE, etc.
            "limit": args.get("limit", 100),
            "offset": args.get("offset", 0),
        }

        result = self._make_request("GET", "/payments", access_token, params)

        return {
            "payments": [
                {
                    "payment_id": p.get("paymentId"),
                    "status": p.get("status"),
                    "payment_method": p.get("paymentMethod"),
                    "amount": p.get("amount"),
                    "beneficiary_name": p.get("beneficiary", {}).get("name"),
                    "execution_date": p.get("executionDate"),
                    "completion_date": p.get("completionDate"),
                }
                for p in result.get("payments", [])
            ],
            "total_count": result.get("totalCount"),
        }

    def create_recipient(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a payment recipient/beneficiary"""
        access_token = self._get_access_token(args)

        recipient_data = {
            "name": args.get("name"),
            "email": args.get("email"),
            "phone": args.get("phone"),
            "accountDetails": {
                "accountNumber": args.get("account_number"),
                "routingNumber": args.get("routing_number"),
                "accountType": args.get("account_type", "checking"),
                "bankName": args.get("bank_name"),
            },
            "address": {
                "line1": args.get("address_line1"),
                "city": args.get("city"),
                "state": args.get("state"),
                "postalCode": args.get("postal_code"),
                "country": args.get("country", "US"),
            },
        }

        result = self._make_request("POST", "/recipients", access_token, recipient_data)

        return {
            "recipient_id": result.get("recipientId"),
            "name": result.get("name"),
            "status": result.get("status"),
            "created_date": result.get("createdDate"),
        }
