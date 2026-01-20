"""
Shopify connector - Shop operations
"""

from typing import Any

from app.http_client import http_client


class ShopifyShopMixin:
    """Shopify shop operations mixin"""

    def get_shop(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get shop information"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        if not shop_domain:
            raise ValueError("shop_domain is required but not found in credentials or args")
        base_url = self._get_base_url(shop_domain)

        result = http_client.get(
            url=f"{base_url}/shop.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        shop = result.get("shop", result)
        shop_id = shop.get("id")
        return {
            "id": str(shop_id) if shop_id is not None else None,
            "name": shop.get("name"),
            "email": shop.get("email"),
            "domain": shop.get("domain"),
            "currency": shop.get("currency"),
            "timezone": shop.get("timezone"),
            "plan_name": shop.get("plan_name"),
        }
