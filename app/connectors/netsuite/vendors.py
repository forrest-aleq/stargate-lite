"""
Vendor operations for NetSuite connector.
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .journal_entries import JournalEntriesMixin

logger = get_logger(__name__)


class VendorsMixin(JournalEntriesMixin):
    """Mixin with vendor operations."""

    def get_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get vendor details from NetSuite"""
        logger.info(
            "Getting vendor",
            service="netsuite",
            vendor_id=args.get("vendor_id"),
            log_event="netsuite_vendor_get",
        )
        cred = self._get_credentials(org_id, user_id)

        vendor_id = str(args.get("vendor_id", "")).replace("ns:", "")
        if not vendor_id:
            raise ValidationError("vendor_id", "is required")

        result = self._make_request("GET", f"record/v1/vendor/{vendor_id}", cred)

        return {
            "vendor_id": f"ns:{result.get('id')}",
            "company_name": result.get("companyName"),
            "email": result.get("email"),
            "phone": result.get("phone"),
            "balance": result.get("balance", 0),
        }

    def create_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a vendor in NetSuite"""
        logger.info(
            "Creating vendor",
            service="netsuite",
            company_name=args.get("company_name"),
            log_event="netsuite_vendor_create",
        )
        cred = self._get_credentials(org_id, user_id)

        company_name = args.get("company_name")
        if not company_name:
            raise ValidationError("company_name", "is required")

        vendor_data: dict[str, Any] = {
            "companyName": company_name,
        }

        if args.get("email"):
            vendor_data["email"] = args["email"]
        if args.get("phone"):
            vendor_data["phone"] = args["phone"]
        if args.get("terms"):
            vendor_data["terms"] = {"id": str(args["terms"])}
        if args.get("account_number"):
            vendor_data["accountNumber"] = args["account_number"]
        if args.get("subsidiary_id"):
            vendor_data["subsidiary"] = {"id": str(args["subsidiary_id"])}

        result = self._make_request("POST", "record/v1/vendor", cred, vendor_data)

        logger.info(
            "Vendor created",
            service="netsuite",
            vendor_id=result.get("id"),
            log_event="netsuite_vendor_created",
        )

        return {
            "vendor_id": f"ns:{result.get('id')}",
            "company_name": result.get("companyName"),
            "status": "active",
        }

    def update_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update vendor record (address, phone, email, etc.)"""
        cred = self._get_credentials(org_id, user_id)

        vendor_id = str(args.get("vendor_id", "")).replace("ns:", "")
        if not vendor_id:
            raise ValidationError("vendor_id", "is required")

        # Build update data from provided fields
        update_data: dict[str, Any] = {}

        if args.get("company_name"):
            update_data["companyName"] = args["company_name"]
        if args.get("email"):
            update_data["email"] = args["email"]
        if args.get("phone"):
            update_data["phone"] = args["phone"]
        if args.get("address"):
            # NetSuite REST API address structure
            addr = args["address"]
            update_data["addressbook"] = {
                "items": [
                    {
                        "addressbookAddress": {
                            "addr1": addr.get("street1"),
                            "addr2": addr.get("street2", ""),
                            "city": addr.get("city"),
                            "state": addr.get("state"),
                            "zip": addr.get("zip"),
                            "country": {"id": addr.get("country", "_unitedStates")},
                        }
                    }
                ]
            }
        if args.get("terms"):
            update_data["terms"] = {"id": str(args["terms"])}
        if args.get("account_number"):
            update_data["accountNumber"] = args["account_number"]

        result = self._make_request("PATCH", f"record/v1/vendor/{vendor_id}", cred, update_data)

        return {
            "vendor_id": f"ns:{result.get('id')}",
            "company_name": result.get("companyName"),
            "status": "updated",
        }

    def query_vendor_by_name(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Search for vendors by company name"""
        vendor_name = args.get("vendor_name", "")
        if not vendor_name:
            raise ValidationError("vendor_name", "is required for search")

        # Sanitize input to prevent SQL injection - escape single quotes
        # Note: SuiteQL doesn't support parameterized queries, so we use escaping
        vendor_name_safe = vendor_name.replace("'", "''")

        # Use SuiteQL to search vendors
        # nosec B608: Input sanitized via quote escaping, SuiteQL doesn't support parameterization
        query = (
            "SELECT id, companyname, email, phone FROM vendor "
            "WHERE LOWER(companyname) LIKE LOWER('%" + vendor_name_safe + "%') "
            "AND isinactive = 'F'"
        )

        result = self.query_records(
            org_id, user_id, {"query": query, "limit": args.get("limit", 20)}
        )

        return {
            "vendors": [
                {
                    "vendor_id": f"ns:{item['id']}",
                    "company_name": item.get("companyname"),
                    "email": item.get("email"),
                    "phone": item.get("phone"),
                }
                for item in result.get("items", [])
            ],
            "count": result.get("count", 0),
        }

    def create_custom_record(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a custom record in NetSuite"""
        cred = self._get_credentials(org_id, user_id)

        record_type = args.get("record_type")  # e.g., "customrecord_myrecord"
        if not isinstance(record_type, str) or not record_type:
            raise ValidationError("record_type", "is required and must be a string")
        field_data = args.get("fields", {})

        result = self._make_request("POST", f"record/v1/{record_type}", cred, field_data)

        return {
            "record_id": f"ns:{result.get('id')}",
            "record_type": record_type,
            "status": "created",
        }
