"""
Shopify connector - Product operations
"""

from typing import Any
from urllib.parse import urlencode

from app.http_client import http_client


class ShopifyProductsMixin:
    """Shopify product operations mixin"""

    def list_products(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List products from Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        params = {}
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("product_type"):
            params["product_type"] = args["product_type"]
        if args.get("vendor"):
            params["vendor"] = args["vendor"]
        if args.get("limit"):
            params["limit"] = min(args["limit"], 250)

        url = f"{base_url}/products.json"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        products = result.get("products", [])
        return {
            "products": [
                {
                    "id": str(p["id"]),
                    "title": p.get("title"),
                    "vendor": p.get("vendor"),
                    "product_type": p.get("product_type"),
                    "variants": p.get("variants", []),
                }
                for p in products
            ],
            "count": len(products),
        }

    def get_product(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get product details"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        product_id = args["product_id"]

        result = http_client.get(
            url=f"{base_url}/products/{product_id}.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        p = result.get("product", result)
        return {
            "id": str(p["id"]),
            "title": p.get("title"),
            "body_html": p.get("body_html"),
            "vendor": p.get("vendor"),
            "product_type": p.get("product_type"),
            "status": p.get("status"),
            "variants": p.get("variants", []),
            "images": p.get("images", []),
        }

    def create_product(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a product in Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        product_data = {"title": args["title"]}
        if args.get("body_html"):
            product_data["body_html"] = args["body_html"]
        if args.get("vendor"):
            product_data["vendor"] = args["vendor"]
        if args.get("product_type"):
            product_data["product_type"] = args["product_type"]
        if args.get("variants"):
            product_data["variants"] = args["variants"]
        if args.get("status"):
            product_data["status"] = args["status"]

        result = http_client.post(
            url=f"{base_url}/products.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
            json={"product": product_data},
        )

        p = result.get("product", result)
        return {
            "id": str(p["id"]),
            "title": p.get("title"),
        }

    def list_inventory(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List inventory levels"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        params = {}
        if args.get("inventory_item_ids"):
            params["inventory_item_ids"] = ",".join(str(i) for i in args["inventory_item_ids"])
        if args.get("location_ids"):
            params["location_ids"] = ",".join(str(i) for i in args["location_ids"])

        url = f"{base_url}/inventory_levels.json"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        levels = result.get("inventory_levels", [])
        return {
            "inventory_levels": levels,
            "count": len(levels),
        }
