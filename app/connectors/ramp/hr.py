"""
Ramp HR mixin for users, departments, locations, and spend programs.
"""

from typing import Any

from .treasury import TreasuryMixin


class HRMixin(TreasuryMixin):
    """Mixin with HR and organizational operations."""

    def get_users(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List Ramp users."""
        result = self._make_request("GET", "/users", org_id, user_id)

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

    def create_reimbursement(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create an expense reimbursement."""
        reimbursement_data = {
            "user_id": args.get("ramp_user_id"),
            "amount": args.get("amount"),
            "merchant_name": args.get("merchant_name"),
            "transaction_date": args.get("transaction_date"),
            "receipts": args.get("receipts", []),
        }

        result = self._make_request(
            "POST", "/reimbursements", org_id, user_id, data=reimbursement_data
        )

        return {
            "reimbursement_id": result["id"],
            "amount": result["amount"],
            "status": result["status"],
        }

    def list_reimbursements(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List reimbursements."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/reimbursements", org_id, user_id, params=params)

        return {
            "reimbursements": [
                {
                    "id": r["id"],
                    "amount": r.get("amount"),
                    "status": r.get("status"),
                    "user_id": r.get("user_id"),
                    "merchant_name": r.get("merchant_name"),
                }
                for r in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def list_departments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List departments."""
        result = self._make_request("GET", "/departments", org_id, user_id)

        return {
            "departments": [
                {
                    "id": d["id"],
                    "name": d.get("name"),
                }
                for d in result.get("data", [])
            ],
        }

    def get_department(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single department by ID."""
        department_id = args.get("department_id")
        result = self._make_request("GET", f"/departments/{department_id}", org_id, user_id)

        return {
            "id": result["id"],
            "name": result.get("name"),
        }

    def list_locations(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List locations."""
        result = self._make_request("GET", "/locations", org_id, user_id)

        return {
            "locations": [
                {
                    "id": loc["id"],
                    "name": loc.get("name"),
                }
                for loc in result.get("data", [])
            ],
        }

    def get_location(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single location by ID."""
        location_id = args.get("location_id")
        result = self._make_request("GET", f"/locations/{location_id}", org_id, user_id)

        return {
            "id": result["id"],
            "name": result.get("name"),
            "address": result.get("address"),
        }

    def list_merchants(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List merchants."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/merchants", org_id, user_id, params=params)

        return {
            "merchants": [
                {
                    "id": m["id"],
                    "name": m.get("name"),
                    "category": m.get("category"),
                }
                for m in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def get_merchant(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single merchant by ID."""
        merchant_id = args.get("merchant_id")
        result = self._make_request("GET", f"/merchants/{merchant_id}", org_id, user_id)

        return {
            "id": result["id"],
            "name": result.get("name"),
            "category": result.get("category"),
        }

    def list_receipts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List receipts."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/receipts", org_id, user_id, params=params)

        return {
            "receipts": [
                {
                    "id": r["id"],
                    "transaction_id": r.get("transaction_id"),
                    "status": r.get("status"),
                }
                for r in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def get_receipt(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single receipt by ID."""
        receipt_id = args.get("receipt_id")
        result = self._make_request("GET", f"/receipts/{receipt_id}", org_id, user_id)

        return {
            "id": result["id"],
            "transaction_id": result.get("transaction_id"),
            "status": result.get("status"),
            "urls": result.get("urls", []),
        }

    def list_spend_programs(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List spend programs."""
        result = self._make_request("GET", "/spend-programs", org_id, user_id)

        return {
            "spend_programs": [
                {
                    "id": sp["id"],
                    "name": sp.get("name"),
                    "status": sp.get("status"),
                }
                for sp in result.get("data", [])
            ],
        }

    def list_limits(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List spending limits."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/limits", org_id, user_id, params=params)

        return {
            "limits": [
                {
                    "id": lim["id"],
                    "display_name": lim.get("display_name"),
                    "amount": lim.get("amount"),
                    "interval": lim.get("interval"),
                }
                for lim in result.get("data", [])
            ],
            "page": result.get("page"),
        }
