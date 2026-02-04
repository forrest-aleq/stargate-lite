"""
Ramp accounting mixin for vendors, bills, and accounting operations.
Vendors are under /accounting/vendors per Ramp API docs.
"""

from typing import Any

from .cards import CardsMixin


class AccountingMixin(CardsMixin):
    """Mixin with vendor, bill, and accounting operations."""

    def list_vendors(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List accounting vendors."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/accounting/vendors", org_id, user_id, params=params)

        return {
            "vendors": [
                {
                    "id": v["id"],
                    "name": v.get("name"),
                    "email": v.get("email"),
                }
                for v in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def get_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single accounting vendor by ID."""
        vendor_id = args.get("vendor_id")
        result = self._make_request("GET", f"/accounting/vendors/{vendor_id}", org_id, user_id)

        return {
            "id": result["id"],
            "name": result.get("name"),
            "email": result.get("email"),
            "address": result.get("address"),
        }

    def list_bills(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bills."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/bills", org_id, user_id, params=params)

        return {
            "bills": [
                {
                    "id": b["id"],
                    "amount": b.get("amount"),
                    "vendor_name": b.get("vendor_name"),
                    "status": b.get("status"),
                    "due_date": b.get("due_date"),
                }
                for b in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def get_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single bill by ID."""
        bill_id = args.get("bill_id")
        result = self._make_request("GET", f"/bills/{bill_id}", org_id, user_id)

        return {
            "id": result["id"],
            "amount": result.get("amount"),
            "vendor_name": result.get("vendor_name"),
            "status": result.get("status"),
            "due_date": result.get("due_date"),
            "invoice_number": result.get("invoice_number"),
        }

    def get_accounting_connection(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get active accounting connection."""
        result = self._make_request("GET", "/accounting/connection", org_id, user_id)

        return {
            "id": result.get("id"),
            "provider": result.get("provider"),
            "status": result.get("status"),
        }

    def list_accounting_gl_accounts(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List GL accounts from connected accounting provider."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/accounting/accounts", org_id, user_id, params=params)

        return {
            "gl_accounts": [
                {
                    "id": a["id"],
                    "name": a.get("name"),
                    "code": a.get("code"),
                    "type": a.get("type"),
                }
                for a in result.get("data", [])
            ],
            "page": result.get("page"),
        }
