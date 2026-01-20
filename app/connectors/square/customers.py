"""
Square connector - Customer operations
"""

from typing import Any

from app.http_client import http_client


class SquareCustomersMixin:
    """Square customer operations mixin"""

    def list_customers(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List customers from Square"""
        cred = self._get_access_token(org_id, user_id)

        params = {}
        if args.get("cursor"):
            params["cursor"] = args["cursor"]
        if args.get("limit"):
            params["limit"] = args["limit"]
        if args.get("sort_field"):
            params["sort_field"] = args["sort_field"]
        if args.get("sort_order"):
            params["sort_order"] = args["sort_order"]

        result = http_client.get(
            url=f"{self.base_url}/customers",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            params=params,
        )

        customers = result.get("customers", [])
        return {
            "customers": [
                {
                    "id": c["id"],
                    "given_name": c.get("given_name"),
                    "family_name": c.get("family_name"),
                    "email_address": c.get("email_address"),
                    "phone_number": c.get("phone_number"),
                }
                for c in customers
            ],
            "cursor": result.get("cursor"),
        }

    def get_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get customer details"""
        cred = self._get_access_token(org_id, user_id)
        customer_id = args["customer_id"]

        result = http_client.get(
            url=f"{self.base_url}/customers/{customer_id}",
            service="square",
            headers=self._get_headers(cred["access_token"]),
        )

        c = result.get("customer", result)
        return {
            "id": c["id"],
            "given_name": c.get("given_name"),
            "family_name": c.get("family_name"),
            "email_address": c.get("email_address"),
            "phone_number": c.get("phone_number"),
            "company_name": c.get("company_name"),
            "created_at": c.get("created_at"),
        }

    def create_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a customer in Square"""
        cred = self._get_access_token(org_id, user_id)

        customer_data = {
            "idempotency_key": args["idempotency_key"],
        }
        if args.get("given_name"):
            customer_data["given_name"] = args["given_name"]
        if args.get("family_name"):
            customer_data["family_name"] = args["family_name"]
        if args.get("company_name"):
            customer_data["company_name"] = args["company_name"]
        if args.get("email_address"):
            customer_data["email_address"] = args["email_address"]
        if args.get("phone_number"):
            customer_data["phone_number"] = args["phone_number"]
        if args.get("reference_id"):
            customer_data["reference_id"] = args["reference_id"]
        if args.get("note"):
            customer_data["note"] = args["note"]

        result = http_client.post(
            url=f"{self.base_url}/customers",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=customer_data,
        )

        c = result.get("customer", result)
        return {
            "customer_id": c["id"],
        }
