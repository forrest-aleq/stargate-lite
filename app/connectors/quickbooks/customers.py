"""
QuickBooks Online connector - Customers module
"""

from typing import Any

from app.http_client import http_client


class QuickBooksCustomersMixin:
    """QuickBooks customer operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a customer in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        customer_data: dict[str, Any] = {"DisplayName": args.get("customer_name")}

        if args.get("email"):
            customer_data["PrimaryEmailAddr"] = {"Address": args["email"]}
        if args.get("phone"):
            customer_data["PrimaryPhone"] = {"FreeFormNumber": args["phone"]}
        if args.get("company_name"):
            customer_data["CompanyName"] = args["company_name"]
        if args.get("billing_address"):
            customer_data["BillAddr"] = args["billing_address"]
        if args.get("shipping_address"):
            customer_data["ShipAddr"] = args["shipping_address"]

        url = f"{self.base_url}/{realm_id}/customer"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=customer_data,
        )

        customer = result.get("Customer", {})
        return {
            "customer_id": f"qb:{customer.get('Id')}",
            "display_name": customer.get("DisplayName"),
            "email": customer.get("PrimaryEmailAddr", {}).get("Address"),
            "balance": customer.get("Balance", 0),
            "created_at": customer.get("MetaData", {}).get("CreateTime"),
        }

    def get_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get customer details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/customer/{customer_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        customer = result.get("Customer", {})
        return {
            "customer_id": f"qb:{customer.get('Id')}",
            "display_name": customer.get("DisplayName"),
            "email": customer.get("PrimaryEmailAddr", {}).get("Address"),
            "phone": customer.get("PrimaryPhone", {}).get("FreeFormNumber"),
            "balance": customer.get("Balance", 0),
            "status": "active" if customer.get("Active") else "inactive",
        }

    def update_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a customer in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/customer/{customer_id}"
        customer_response = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )
        customer_full = customer_response.get("Customer", {})

        update_data: dict[str, Any] = {
            "Id": customer_id,
            "SyncToken": customer_full.get("SyncToken"),
        }

        if args.get("customer_name"):
            update_data["DisplayName"] = args["customer_name"]
        if args.get("email"):
            update_data["PrimaryEmailAddr"] = {"Address": args["email"]}
        if args.get("phone"):
            update_data["PrimaryPhone"] = {"FreeFormNumber": args["phone"]}

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

        customer = result.get("Customer", {})
        return {
            "customer_id": f"qb:{customer.get('Id')}",
            "display_name": customer.get("DisplayName"),
            "updated": True,
        }

    def list_customers(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List customers from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Customer"
        if args.get("active_only"):
            query += " WHERE Active = true"
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        customers = result.get("QueryResponse", {}).get("Customer", [])
        return {
            "customers": [
                {
                    "customer_id": f"qb:{c.get('Id')}",
                    "display_name": c.get("DisplayName"),
                    "email": c.get("PrimaryEmailAddr", {}).get("Address"),
                    "balance": c.get("Balance", 0),
                }
                for c in customers
            ],
            "count": len(customers),
        }

    def search_customers(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search customers by name with fuzzy matching"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        search_term = args.get("search_term", args.get("name", ""))
        max_results = args.get("max_results", 25)

        query = f"SELECT * FROM Customer WHERE DisplayName LIKE '%{search_term}%'"
        query += f" MAXRESULTS {max_results}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        customers = result.get("QueryResponse", {}).get("Customer", [])
        return {
            "customers": [
                {
                    "customer_id": f"qb:{c.get('Id')}",
                    "display_name": c.get("DisplayName"),
                    "email": c.get("PrimaryEmailAddr", {}).get("Address"),
                    "balance": c.get("Balance", 0),
                }
                for c in customers
            ],
            "count": len(customers),
            "search_term": search_term,
        }
