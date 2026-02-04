"""
Ramp transactions mixin for transaction operations.
"""

from typing import Any

from .base import RampBase


class TransactionsMixin(RampBase):
    """Mixin with transaction operations."""

    def list_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List card transactions."""
        params = {
            "start": args.get("start_date"),
            "end": args.get("end_date"),
            "page_size": args.get("page_size", 50),
        }

        result = self._make_request("GET", "/transactions", org_id, user_id, params=params)

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

    def get_transaction(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single transaction by ID."""
        transaction_id = args.get("transaction_id")
        result = self._make_request("GET", f"/transactions/{transaction_id}", org_id, user_id)

        return {
            "id": result["id"],
            "amount": result["amount"],
            "merchant_name": result.get("merchant_name"),
            "card_id": result.get("card_id"),
            "user_id": result.get("user_id"),
            "state": result["state"],
            "created_at": result["created_at"],
            "receipts": result.get("receipts", []),
            "memo": result.get("memo"),
        }
