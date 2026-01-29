"""
QuickBooks Online connector - Vendors module
"""

from typing import Any

from app.connectors.quickbooks import deep_links
from app.http_client import http_client


class QuickBooksVendorsMixin:
    """QuickBooks vendor operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a vendor in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        vendor_data: dict[str, Any] = {
            "DisplayName": args.get("vendor_name"),
            "PrimaryEmailAddr": {"Address": args.get("email")},
        }

        if args.get("phone"):
            vendor_data["PrimaryPhone"] = {"FreeFormNumber": args["phone"]}
        if args.get("website"):
            vendor_data["WebAddr"] = {"URI": args["website"]}
        if args.get("billing_address"):
            vendor_data["BillAddr"] = args["billing_address"]

        url = f"{self.base_url}/{realm_id}/vendor"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=vendor_data,
        )

        vendor = result.get("Vendor", {})
        vendor_id = vendor.get("Id")

        return {
            "vendor_id": f"qb:{vendor_id}",
            "display_name": vendor.get("DisplayName"),
            "email": vendor.get("PrimaryEmailAddr", {}).get("Address"),
            "status": "active",
            "created_at": vendor.get("MetaData", {}).get("CreateTime"),
            "deep_link": deep_links.vendor_link(vendor_id),
        }

    def get_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get vendor details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        vendor_id = args.get("vendor_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/vendor/{vendor_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        vendor = result.get("Vendor", {})
        vid = vendor.get("Id")

        return {
            "vendor_id": f"qb:{vid}",
            "display_name": vendor.get("DisplayName"),
            "email": vendor.get("PrimaryEmailAddr", {}).get("Address"),
            "phone": vendor.get("PrimaryPhone", {}).get("FreeFormNumber"),
            "status": "active" if vendor.get("Active") else "inactive",
            "deep_link": deep_links.vendor_link(vid),
        }

    def list_vendors(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List vendors from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        max_results = args.get("max_results", 100)
        start_position = args.get("start_position", 1)
        active_only = args.get("active_only", True)

        query = f"SELECT * FROM Vendor WHERE Active = {str(active_only).lower()}"
        query += f" STARTPOSITION {start_position} MAXRESULTS {max_results}"

        url = f"{self.base_url}/{realm_id}/query"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
            params={"query": query},
        )

        vendors = result.get("QueryResponse", {}).get("Vendor", [])

        return {
            "vendors": [
                {
                    "vendor_id": f"qb:{v.get('Id')}",
                    "display_name": v.get("DisplayName"),
                    "email": v.get("PrimaryEmailAddr", {}).get("Address"),
                    "status": "active" if v.get("Active") else "inactive",
                    "deep_link": deep_links.vendor_link(v.get("Id")),
                }
                for v in vendors
            ],
            "count": len(vendors),
        }

    def update_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a vendor in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        vendor_id = args.get("vendor_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/vendor/{vendor_id}"
        vendor_response = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )
        vendor_full = vendor_response.get("Vendor", {})

        update_data: dict[str, Any] = {
            "Id": vendor_id,
            "SyncToken": vendor_full.get("SyncToken"),
        }

        if args.get("vendor_name"):
            update_data["DisplayName"] = args["vendor_name"]
        if args.get("email"):
            update_data["PrimaryEmailAddr"] = {"Address": args["email"]}
        if args.get("phone"):
            update_data["PrimaryPhone"] = {"FreeFormNumber": args["phone"]}
        if args.get("website"):
            update_data["WebAddr"] = {"URI": args["website"]}
        if args.get("billing_address"):
            update_data["BillAddr"] = args["billing_address"]

        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=update_data,
        )

        vendor = result.get("Vendor", {})
        vid = vendor.get("Id")
        return {
            "vendor_id": f"qb:{vid}",
            "display_name": vendor.get("DisplayName"),
            "updated": True,
            "deep_link": deep_links.vendor_link(vid),
        }

    def search_vendors(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search vendors by name with fuzzy matching"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        search_term = args.get("search_term", args.get("name", ""))
        max_results = args.get("max_results", 25)

        query = f"SELECT * FROM Vendor WHERE DisplayName LIKE '%{search_term}%'"
        query += f" MAXRESULTS {max_results}"

        url = f"{self.base_url}/{realm_id}/query"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
            params={"query": query},
        )

        vendors = result.get("QueryResponse", {}).get("Vendor", [])

        return {
            "vendors": [
                {
                    "vendor_id": f"qb:{v.get('Id')}",
                    "display_name": v.get("DisplayName"),
                    "email": v.get("PrimaryEmailAddr", {}).get("Address"),
                    "status": "active" if v.get("Active") else "inactive",
                    "deep_link": deep_links.vendor_link(v.get("Id")),
                }
                for v in vendors
            ],
            "count": len(vendors),
            "search_term": search_term,
        }
