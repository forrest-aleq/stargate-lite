"""
Sage Intacct Vendor management connector.

Reference: https://developer.sage.com/intacct/docs/

Provides:
- Vendor CRUD operations
- Vendor formatting utilities
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .gl import GLMixin

logger = get_logger(__name__)


class VendorMixin(GLMixin):
    """Mixin providing Vendor management capabilities."""

    def list_vendors(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List vendors.

        Args:
            status: Filter by status - "active", "inactive"
            vendor_type: Filter by vendor type
            page_size: Results per page (default 100)
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("status"):
            filters.append(f'status eq "{args["status"]}"')
        if args.get("vendor_type"):
            filters.append(f'vendorType eq "{args["vendor_type"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        vendors = self._paginate("objects/vendor", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct vendors listed",
            service="sage_intacct",
            count=len(vendors),
            log_event="vendors_listed",
        )

        return {
            "vendors": [self._format_vendor(v) for v in vendors],
            "count": len(vendors),
            "status": "success",
        }

    def get_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific vendor.

        Args:
            vendor_id: Vendor ID (required)
        """
        cred = self._get_access_token(org_id, user_id)

        vendor_id = args.get("vendor_id")
        if not vendor_id:
            raise ValidationError("vendor_id", "vendor_id is required")

        result = self._make_api_call("GET", f"objects/vendor/{vendor_id}", cred)
        vendor = result.get("ia::result", {})

        if not vendor:
            return {"vendor": None, "status": "not_found"}

        return {"vendor": self._format_vendor(vendor), "status": "success"}

    def create_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new vendor.

        Args:
            vendor_id: Vendor ID (required)
            name: Vendor name (required)
            display_contact_name: Display name
            status: "active" or "inactive" (default "active")
            vendor_type: Vendor type
            tax_id: Tax ID (EIN/SSN)
            payment_term: Payment term key
            default_expense_account: Default GL account for expenses
            email: Email address
            phone: Phone number
            address: Address object
                - line1, line2, city, state, postal_code, country
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("vendor_id"):
            raise ValidationError("vendor_id", "vendor_id is required")
        if not args.get("name"):
            raise ValidationError("name", "name is required")

        vendor_data: dict[str, Any] = {
            "id": args["vendor_id"],
            "name": args["name"],
        }

        if args.get("display_contact_name"):
            vendor_data["displayContact"] = {"contactName": args["display_contact_name"]}
        if args.get("status"):
            vendor_data["status"] = args["status"]
        if args.get("vendor_type"):
            vendor_data["vendorType"] = {"id": args["vendor_type"]}
        if args.get("tax_id"):
            vendor_data["taxId"] = args["tax_id"]
        if args.get("payment_term"):
            vendor_data["paymentTerm"] = {"key": args["payment_term"]}
        if args.get("default_expense_account"):
            vendor_data["defaultExpenseGLAccount"] = {"accountNo": args["default_expense_account"]}

        if args.get("email"):
            vendor_data["primaryContact"] = vendor_data.get("primaryContact", {})
            vendor_data["primaryContact"]["email1"] = args["email"]
        if args.get("phone"):
            vendor_data["primaryContact"] = vendor_data.get("primaryContact", {})
            vendor_data["primaryContact"]["phone1"] = args["phone"]

        if args.get("address"):
            addr = args["address"]
            vendor_data["mailingAddress"] = {
                "addressLine1": addr.get("line1"),
                "addressLine2": addr.get("line2"),
                "city": addr.get("city"),
                "state": addr.get("state"),
                "postCode": addr.get("postal_code"),
                "country": addr.get("country"),
            }

        result = self._make_api_call("POST", "objects/vendor", cred, data=vendor_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct vendor created",
            service="sage_intacct",
            vendor_id=args["vendor_id"],
            log_event="vendor_created",
        )

        return {"vendor": self._format_vendor(created), "status": "success"}

    def update_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing vendor.

        Args:
            vendor_id: Vendor ID (required)
            name: Updated name
            status: Updated status
            ... (other fields as in create_vendor)
        """
        cred = self._get_access_token(org_id, user_id)

        vendor_id = args.get("vendor_id")
        if not vendor_id:
            raise ValidationError("vendor_id", "vendor_id is required")

        vendor_data: dict[str, Any] = {}

        if args.get("name"):
            vendor_data["name"] = args["name"]
        if args.get("status"):
            vendor_data["status"] = args["status"]
        if args.get("vendor_type"):
            vendor_data["vendorType"] = {"id": args["vendor_type"]}
        if args.get("payment_term"):
            vendor_data["paymentTerm"] = {"key": args["payment_term"]}
        if args.get("email"):
            vendor_data["primaryContact"] = {"email1": args["email"]}

        result = self._make_api_call("PATCH", f"objects/vendor/{vendor_id}", cred, data=vendor_data)
        updated = result.get("ia::result", {})

        logger.info(
            "Sage Intacct vendor updated",
            service="sage_intacct",
            vendor_id=vendor_id,
            log_event="vendor_updated",
        )

        return {"vendor": self._format_vendor(updated), "status": "success"}

    def _format_vendor(self, vendor: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct vendor for API response."""
        contact = vendor.get("primaryContact", {})
        address = vendor.get("mailingAddress", {})

        return {
            "key": vendor.get("key"),
            "vendor_id": vendor.get("id"),
            "name": vendor.get("name"),
            "display_name": vendor.get("displayContact", {}).get("contactName"),
            "status": vendor.get("status"),
            "vendor_type": vendor.get("vendorType", {}).get("id"),
            "tax_id": vendor.get("taxId"),
            "payment_term": vendor.get("paymentTerm", {}).get("key"),
            "default_expense_account": vendor.get("defaultExpenseGLAccount", {}).get("accountNo"),
            "email": contact.get("email1"),
            "phone": contact.get("phone1"),
            "address": {
                "line1": address.get("addressLine1"),
                "line2": address.get("addressLine2"),
                "city": address.get("city"),
                "state": address.get("state"),
                "postal_code": address.get("postCode"),
                "country": address.get("country"),
            },
            "total_due": vendor.get("totalDue"),
            "href": vendor.get("href"),
        }
