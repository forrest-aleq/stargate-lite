"""Bill.com vendor operations."""

import time
from typing import Any

from app.connectors.billcom.base import BillComBase
from app.errors import ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


class BillComVendorsMixin(BillComBase):
    """Vendor operations for Bill.com."""

    def create_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a vendor in Bill.com."""
        start_time = time.time()

        vendor_data: dict[str, Any] = {"name": args["vendor_name"]}

        if args.get("email"):
            vendor_data["email"] = args["email"]
        if args.get("phone"):
            vendor_data["phone"] = args["phone"]
        if args.get("account_number"):
            vendor_data["accountNumber"] = args["account_number"]
        if args.get("address"):
            vendor_data["address"] = args["address"]
        if args.get("payment_terms"):
            vendor_data["paymentTerms"] = args["payment_terms"]

        result = self._api_call("POST", "/vendors", org_id, user_id, json_data=vendor_data)

        logger.info(
            "Created Bill.com vendor",
            service="billcom",
            vendor_id=result.get("id"),
            duration_ms=round((time.time() - start_time) * 1000, 2),
            log_event="vendor_created",
        )

        return {
            "vendor_id": f"bc:{result['id']}",
            "vendor_name": result.get("name"),
            "email": result.get("email"),
            "status": result.get("status"),
            "network_status": result.get("networkStatus"),
        }

    def get_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single vendor by ID."""
        vendor_id = args["vendor_id"].replace("bc:", "")
        result = self._api_call("GET", f"/vendors/{vendor_id}", org_id, user_id)

        return {
            "vendor_id": f"bc:{result['id']}",
            "vendor_name": result.get("name"),
            "email": result.get("email"),
            "phone": result.get("phone"),
            "account_number": result.get("accountNumber"),
            "status": result.get("status"),
            "network_status": result.get("networkStatus"),
            "address": result.get("address"),
            "payment_terms": result.get("paymentTerms"),
            "created_at": result.get("createdTime"),
            "updated_at": result.get("updatedTime"),
        }

    def list_vendors(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List vendors from Bill.com."""
        params: dict[str, Any] = {"max": min(args.get("page_size", 50), 100)}

        if args.get("page"):
            params["page"] = args["page"]
        if args.get("status"):
            params["status"] = args["status"]

        result = self._api_call("GET", "/vendors", org_id, user_id, params=params)

        return {
            "vendors": [
                {
                    "vendor_id": f"bc:{v['id']}",
                    "vendor_name": v.get("name"),
                    "email": v.get("email"),
                    "status": v.get("status"),
                    "network_status": v.get("networkStatus"),
                }
                for v in result.get("results", [])
            ],
            "next_page": result.get("nextPage"),
            "prev_page": result.get("prevPage"),
        }

    def update_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a vendor in Bill.com."""
        vendor_id = args["vendor_id"].replace("bc:", "")

        update_data: dict[str, Any] = {}
        if args.get("vendor_name"):
            update_data["name"] = args["vendor_name"]
        if args.get("email"):
            update_data["email"] = args["email"]
        if args.get("phone"):
            update_data["phone"] = args["phone"]
        if args.get("account_number"):
            update_data["accountNumber"] = args["account_number"]
        if args.get("address"):
            update_data["address"] = args["address"]
        if args.get("payment_terms"):
            update_data["paymentTerms"] = args["payment_terms"]

        if not update_data:
            raise ValidationError("update_data", "No fields provided to update")

        result = self._api_call("PATCH", f"/vendors/{vendor_id}", org_id, user_id, json_data=update_data)

        return {
            "vendor_id": f"bc:{result['id']}",
            "vendor_name": result.get("name"),
            "email": result.get("email"),
            "status": result.get("status"),
            "updated": True,
        }

    def archive_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Archive (soft delete) a vendor."""
        vendor_id = args["vendor_id"].replace("bc:", "")
        result = self._api_call("POST", f"/vendors/{vendor_id}/archive", org_id, user_id, json_data={})

        return {
            "vendor_id": f"bc:{vendor_id}",
            "status": result.get("status", "ARCHIVED"),
            "archived": True,
        }

    def create_vendor_credit(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a vendor credit in Bill.com."""
        vendor_id = args["vendor_id"].replace("bc:", "")

        credit_data: dict[str, Any] = {
            "vendorId": vendor_id,
            "creditDate": args.get("credit_date"),
            "amount": args["amount"],
        }

        if args.get("description"):
            credit_data["description"] = args["description"]
        if args.get("reference_number"):
            credit_data["refNumber"] = args["reference_number"]

        result = self._api_call("POST", "/vendorCredits", org_id, user_id, json_data=credit_data)

        return {
            "credit_id": f"bc:{result['id']}",
            "vendor_id": f"bc:{vendor_id}",
            "amount": result.get("amount"),
            "credit_date": result.get("creditDate"),
            "status": result.get("status"),
        }

    def list_vendor_credits(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List vendor credits from Bill.com."""
        params: dict[str, Any] = {"max": min(args.get("page_size", 50), 100)}

        if args.get("page"):
            params["page"] = args["page"]
        if args.get("vendor_id"):
            params["vendorId"] = args["vendor_id"].replace("bc:", "")

        result = self._api_call("GET", "/vendorCredits", org_id, user_id, params=params)

        return {
            "credits": [
                {
                    "credit_id": f"bc:{c['id']}",
                    "vendor_id": f"bc:{c.get('vendorId', '')}",
                    "amount": c.get("amount"),
                    "credit_date": c.get("creditDate"),
                    "status": c.get("status"),
                }
                for c in result.get("results", [])
            ],
            "next_page": result.get("nextPage"),
            "prev_page": result.get("prevPage"),
        }
