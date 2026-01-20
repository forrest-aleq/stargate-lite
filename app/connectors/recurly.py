"""
Recurly connector for Stargate Lite
Handles subscription billing, invoices, plans
Uses Recurly API v2021-02-25 (October 2025)
"""

import os
from typing import Any, cast

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class RecurlyConnector:
    """Recurly API connector for subscription management"""

    BASE_URL = "https://v3.recurly.com"

    def __init__(self) -> None:
        self.api_key = os.getenv("RECURLY_API_KEY")
        self.subdomain = os.getenv("RECURLY_SUBDOMAIN", "v3")

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.recurly.v2021-02-25",
        }

    def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()

        if method not in ["GET", "POST", "PUT", "DELETE"]:
            raise ValueError(f"Unsupported method: {method}")

        # Handle GET with params vs POST/PUT/DELETE with JSON body
        if method == "GET":
            result = http_client.get(url=url, service="recurly", headers=headers, params=data)
        elif method == "DELETE":
            # DELETE may return 204 No Content
            response = http_client.request(
                method=method, url=url, service="recurly", headers=headers, parse_json=False
            )
            if response.status_code == 204:
                return {"status": "success"}
            # Defensive JSON parsing for non-204 responses
            try:
                return cast(dict[str, Any], response.json())
            except Exception:
                return {"status": "success", "status_code": response.status_code}
        else:
            # POST, PUT
            result = http_client.request(
                method=method, url=url, service="recurly", headers=headers, json=data
            )

        return result

    def create_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a customer account"""
        account_data = {
            "code": args.get("account_code", f"{org_id}_{user_id}"),
            "email": args.get("email"),
            "first_name": args.get("first_name"),
            "last_name": args.get("last_name"),
            "company": args.get("company"),
            "billing_info": args.get("billing_info"),
        }

        result = self._make_request("POST", "/accounts", account_data)

        return {
            "account_id": result["id"],
            "account_code": result["code"],
            "email": result["email"],
            "state": result["state"],
        }

    def create_subscription(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a subscription"""
        subscription_data = {
            "plan_code": args.get("plan_code"),
            "account": {"code": args.get("account_code")},
            "currency": args.get("currency", "USD"),
            # automatic or manual
            "collection_method": args.get("collection_method", "automatic"),
        }

        if args.get("starts_at"):
            subscription_data["starts_at"] = args["starts_at"]

        if args.get("coupon_code"):
            subscription_data["coupon_code"] = args["coupon_code"]

        result = self._make_request("POST", "/subscriptions", subscription_data)

        return {
            "subscription_id": result["id"],
            "uuid": result["uuid"],
            "plan_code": result["plan"]["code"],
            "state": result["state"],
            "current_period_ends_at": result.get("current_period_ends_at"),
            "total": result.get("total"),
        }

    def cancel_subscription(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Cancel a subscription"""
        subscription_id = args.get("subscription_id")
        timeframe = args.get("timeframe", "term_end")  # term_end or now

        result = self._make_request(
            "PUT", f"/subscriptions/{subscription_id}/cancel", {"timeframe": timeframe}
        )

        return {
            "subscription_id": result["id"],
            "state": result["state"],
            "expires_at": result.get("expires_at"),
        }

    def pause_subscription(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Pause a subscription"""
        subscription_id = args.get("subscription_id")

        pause_data = {"remaining_pause_cycles": args.get("remaining_pause_cycles")}

        result = self._make_request("PUT", f"/subscriptions/{subscription_id}/pause", pause_data)

        return {
            "subscription_id": result["id"],
            "state": result["state"],
            "paused_at": result.get("paused_at"),
        }

    def resume_subscription(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Resume a paused subscription"""
        subscription_id = args.get("subscription_id")

        result = self._make_request("PUT", f"/subscriptions/{subscription_id}/resume", {})

        return {"subscription_id": result["id"], "state": result["state"]}

    def list_invoices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List invoices"""
        params = {
            "limit": args.get("limit", 20),
            "state": args.get("state"),  # pending, paid, failed, past_due
        }

        result = self._make_request("GET", "/invoices", params)

        return {
            "invoices": [
                {
                    "invoice_id": inv["id"],
                    "number": inv.get("number"),
                    "account_code": inv.get("account", {}).get("code"),
                    "state": inv["state"],
                    "total": inv.get("total"),
                    "due_at": inv.get("due_at"),
                    "created_at": inv.get("created_at"),
                }
                for inv in result.get("data", [])
            ],
            "has_more": result.get("has_more", False),
        }

    def get_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get invoice details"""
        invoice_id = args.get("invoice_id")

        result = self._make_request("GET", f"/invoices/{invoice_id}")

        return {
            "invoice_id": result["id"],
            "number": result.get("number"),
            "state": result["state"],
            "total": result.get("total"),
            "subtotal": result.get("subtotal"),
            "due_at": result.get("due_at"),
            "line_items": result.get("line_items", []),
        }

    def create_plan(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a subscription plan"""
        plan_data = {
            "code": args.get("plan_code"),
            "name": args.get("plan_name"),
            "currencies": args.get(
                "currencies", [{"currency": "USD", "unit_amount": args.get("price")}]
            ),
            "interval_unit": args.get("interval_unit", "months"),  # months or years
            "interval_length": args.get("interval_length", 1),
        }

        result = self._make_request("POST", "/plans", plan_data)

        return {
            "plan_id": result["id"],
            "plan_code": result["code"],
            "name": result["name"],
            "state": result["state"],
        }

    def list_subscriptions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List subscriptions"""
        params = {
            "limit": args.get("limit", 20),
            "state": args.get("state"),  # active, canceled, expired, etc.
        }

        if args.get("account_code"):
            endpoint = f"/accounts/{args['account_code']}/subscriptions"
        else:
            endpoint = "/subscriptions"

        result = self._make_request("GET", endpoint, params)

        return {
            "subscriptions": [
                {
                    "subscription_id": sub["id"],
                    "plan_code": sub["plan"]["code"],
                    "state": sub["state"],
                    "total": sub.get("total"),
                    "current_period_ends_at": sub.get("current_period_ends_at"),
                }
                for sub in result.get("data", [])
            ],
            "has_more": result.get("has_more", False),
        }

    def apply_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Apply/record an external payment to an invoice.
        Used for lockbox processing - recording check payments received.

        Args:
            invoice_id: The invoice ID to apply payment to
            amount: Payment amount (must match or be less than invoice balance)
            payment_method: Type of payment (check, wire, cash, money_order, external)
            description: Optional description (e.g., check number)
            collected_at: Optional date payment was collected (ISO format)
        """
        invoice_id = args.get("invoice_id")
        if not invoice_id:
            raise ValueError("invoice_id is required")

        amount = args.get("amount")
        if amount is None:
            raise ValueError("amount is required")

        # Build external payment request
        payment_data = {
            "amount": amount,
            "payment_method": args.get("payment_method", "check"),
            "description": args.get("description", ""),
        }

        if args.get("collected_at"):
            payment_data["collected_at"] = args["collected_at"]

        # Record external payment on invoice
        # Recurly API: PUT /invoices/{invoice_id}/mark_paid for full payment
        # or POST /purchases for partial/external payments
        result = self._make_request("PUT", f"/invoices/{invoice_id}/mark_paid", payment_data)

        logger.info(
            "Payment applied to invoice",
            service="recurly",
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_data["payment_method"],
            log_event="recurly_payment_applied",
        )

        return {
            "invoice_id": result.get("id", invoice_id),
            "state": result.get("state", "paid"),
            "amount_applied": amount,
            "payment_method": payment_data["payment_method"],
            "closed_at": result.get("closed_at"),
            "status": "success",
        }

    def collect_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Force collect payment on an invoice using stored billing info.
        Uses the account's default payment method.

        Args:
            invoice_id: The invoice ID to collect
            three_d_secure_action_result_token_id: Optional 3DS token for SCA
        """
        invoice_id = args.get("invoice_id")
        if not invoice_id:
            raise ValueError("invoice_id is required")

        collect_data = {}
        if args.get("three_d_secure_action_result_token_id"):
            token_id = args["three_d_secure_action_result_token_id"]
            collect_data["three_d_secure_action_result_token_id"] = token_id

        result = self._make_request(
            "PUT", f"/invoices/{invoice_id}/collect", collect_data if collect_data else None
        )

        logger.info(
            "Invoice collected",
            service="recurly",
            invoice_id=invoice_id,
            state=result.get("state"),
            log_event="recurly_invoice_collected",
        )

        return {
            "invoice_id": result["id"],
            "state": result["state"],
            "total": result.get("total"),
            "collected_at": result.get("closed_at"),
            "status": "success",
        }

    def search_invoices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Search invoices by account code, invoice number, or state.
        Used for lockbox matching - finding invoices by customer/reference.

        Args:
            account_code: Filter by account code
            invoice_number: Search by invoice number
            state: Filter by state (pending, paid, failed, past_due)
            limit: Max results (default 20)
        """
        params = {"limit": args.get("limit", 20)}

        # Add filters
        if args.get("state"):
            params["state"] = args["state"]

        # If account_code provided, use account-specific endpoint
        if args.get("account_code"):
            endpoint = f"/accounts/{args['account_code']}/invoices"
        else:
            endpoint = "/invoices"

        result = self._make_request("GET", endpoint, params)

        invoices = result.get("data", [])

        # Client-side filter by invoice number if provided
        invoice_number = args.get("invoice_number")
        if invoice_number:
            invoices = [
                inv
                for inv in invoices
                if inv.get("number") and invoice_number.lower() in str(inv["number"]).lower()
            ]

        return {
            "invoices": [
                {
                    "invoice_id": inv["id"],
                    "number": inv.get("number"),
                    "account_code": inv.get("account", {}).get("code"),
                    "account_email": inv.get("account", {}).get("email"),
                    "state": inv["state"],
                    "total": inv.get("total"),
                    "balance": inv.get("balance"),
                    "due_at": inv.get("due_at"),
                    "created_at": inv.get("created_at"),
                }
                for inv in invoices
            ],
            "count": len(invoices),
            "has_more": result.get("has_more", False),
        }
