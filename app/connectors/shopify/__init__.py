"""
Shopify connector package

This package provides a modular Shopify Admin API connector split across multiple files
to maintain code under the 500-line limit per file.

Modules:
- base: Authentication and token refresh
- shop: Shop operations
- orders: Order operations
- customers: Customer operations
- products: Product operations
- fulfillment: Fulfillment operations
- payouts: Payout operations
"""

from app.connectors.shopify.base import ShopifyBase
from app.connectors.shopify.customers import ShopifyCustomersMixin
from app.connectors.shopify.fulfillment import ShopifyFulfillmentMixin
from app.connectors.shopify.orders import ShopifyOrdersMixin
from app.connectors.shopify.payouts import ShopifyPayoutsMixin
from app.connectors.shopify.products import ShopifyProductsMixin
from app.connectors.shopify.shop import ShopifyShopMixin


class ShopifyConnector(
    ShopifyBase,
    ShopifyShopMixin,
    ShopifyOrdersMixin,
    ShopifyCustomersMixin,
    ShopifyProductsMixin,
    ShopifyFulfillmentMixin,
    ShopifyPayoutsMixin,
):
    """
    Shopify Admin API connector.

    This class combines all Shopify operations through mixin classes:
    - Authentication and token management (from ShopifyBase)
    - Shop operations (from ShopifyShopMixin)
    - Order operations (from ShopifyOrdersMixin)
    - Customer operations (from ShopifyCustomersMixin)
    - Product operations (from ShopifyProductsMixin)
    - Fulfillment operations (from ShopifyFulfillmentMixin)
    - Payout operations (from ShopifyPayoutsMixin)
    """

    pass


# Singleton instance
shopify_connector = ShopifyConnector()

__all__ = ["ShopifyConnector", "shopify_connector"]
