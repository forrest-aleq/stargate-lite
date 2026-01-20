"""
Shopify connector - Customer operations
"""

from typing import Any
from urllib.parse import urlencode

from app.http_client import http_client


class ShopifyCustomersMixin:
    """Shopify customer operations mixin"""

    def list_customers(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List customers from Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        params = {}
        if args.get("created_at_min"):
            params["created_at_min"] = args["created_at_min"]
        if args.get("created_at_max"):
            params["created_at_max"] = args["created_at_max"]
        if args.get("limit"):
            params["limit"] = min(args["limit"], 250)

        url = f"{base_url}/customers.json"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        customers = result.get("customers", [])
        return {
            "customers": [
                {
                    "id": str(c["id"]),
                    "email": c.get("email"),
                    "first_name": c.get("first_name"),
                    "last_name": c.get("last_name"),
                    "orders_count": c.get("orders_count"),
                }
                for c in customers
            ],
            "count": len(customers),
        }

    def get_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get customer details"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        customer_id = args["customer_id"]

        result = http_client.get(
            url=f"{base_url}/customers/{customer_id}.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        c = result.get("customer", result)
        return {
            "id": str(c["id"]),
            "email": c.get("email"),
            "first_name": c.get("first_name"),
            "last_name": c.get("last_name"),
            "orders_count": c.get("orders_count"),
            "total_spent": c.get("total_spent"),
            "created_at": c.get("created_at"),
            "addresses": c.get("addresses", []),
        }

    def create_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a customer in Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        customer_data = {"email": args["email"]}
        if args.get("first_name"):
            customer_data["first_name"] = args["first_name"]
        if args.get("last_name"):
            customer_data["last_name"] = args["last_name"]
        if args.get("phone"):
            customer_data["phone"] = args["phone"]
        if args.get("addresses"):
            customer_data["addresses"] = args["addresses"]
        if args.get("send_email_welcome") is not None:
            customer_data["send_email_welcome"] = args["send_email_welcome"]

        result = http_client.post(
            url=f"{base_url}/customers.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
            json={"customer": customer_data},
        )

        c = result.get("customer", result)
        return {
            "id": str(c["id"]),
            "email": c.get("email"),
        }
