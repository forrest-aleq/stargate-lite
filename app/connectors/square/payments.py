"""
Square connector - Payment operations
"""

from typing import Any

from app.http_client import http_client


class SquarePaymentsMixin:
    """Square payment operations mixin"""

    def list_payments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payments from Square"""
        cred = self._get_access_token(org_id, user_id)

        params = {}
        if args.get("location_id"):
            params["location_id"] = args["location_id"]
        if args.get("begin_time"):
            params["begin_time"] = args["begin_time"]
        if args.get("end_time"):
            params["end_time"] = args["end_time"]
        if args.get("sort_order"):
            params["sort_order"] = args["sort_order"]
        if args.get("cursor"):
            params["cursor"] = args["cursor"]
        if args.get("limit"):
            params["limit"] = args["limit"]

        result = http_client.get(
            url=f"{self.base_url}/payments",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            params=params,
        )

        payments = result.get("payments", [])
        return {
            "payments": [
                {
                    "id": p["id"],
                    "amount": p.get("amount_money"),
                    "status": p.get("status"),
                    "source_type": p.get("source_type"),
                    "created_at": p.get("created_at"),
                }
                for p in payments
            ],
            "cursor": result.get("cursor"),
        }

    def get_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get payment details"""
        cred = self._get_access_token(org_id, user_id)
        payment_id = args["payment_id"]

        result = http_client.get(
            url=f"{self.base_url}/payments/{payment_id}",
            service="square",
            headers=self._get_headers(cred["access_token"]),
        )

        p = result.get("payment", result)
        return {
            "id": p["id"],
            "amount_money": p.get("amount_money"),
            "status": p.get("status"),
            "source_type": p.get("source_type"),
            "location_id": p.get("location_id"),
            "order_id": p.get("order_id"),
            "created_at": p.get("created_at"),
            "processing_fee": p.get("processing_fee", []),
            "card_details": p.get("card_details"),
        }

    def create_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a payment in Square"""
        cred = self._get_access_token(org_id, user_id)

        payment_data = {
            "source_id": args["source_id"],
            "amount_money": args["amount_money"],
            "idempotency_key": args["idempotency_key"],
        }
        if args.get("location_id"):
            payment_data["location_id"] = args["location_id"]
        if args.get("customer_id"):
            payment_data["customer_id"] = args["customer_id"]
        if args.get("reference_id"):
            payment_data["reference_id"] = args["reference_id"]
        if args.get("note"):
            payment_data["note"] = args["note"]

        result = http_client.post(
            url=f"{self.base_url}/payments",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=payment_data,
        )

        p = result.get("payment", result)
        return {
            "payment_id": p["id"],
            "status": p.get("status"),
            "receipt_url": p.get("receipt_url"),
        }

    def refund_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Refund a Square payment"""
        cred = self._get_access_token(org_id, user_id)

        refund_data = {
            "payment_id": args["payment_id"],
            "idempotency_key": args["idempotency_key"],
            "amount_money": args["amount_money"],
        }
        if args.get("reason"):
            refund_data["reason"] = args["reason"]

        result = http_client.post(
            url=f"{self.base_url}/refunds",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=refund_data,
        )

        r = result.get("refund", result)
        return {
            "refund_id": r["id"],
            "status": r.get("status"),
            "amount_money": r.get("amount_money"),
        }
