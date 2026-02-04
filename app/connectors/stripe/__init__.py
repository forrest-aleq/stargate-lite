"""
Stripe connector package

This package provides a modular Stripe API connector split across multiple files
to maintain code under the 500-line limit per file.

Modules:
- base: Initialization and configuration
- payments: Payment intents, charges, and refunds
- customers: Customer CRUD operations
- products: Products and prices
- invoices: Invoice operations
- subscriptions: Subscription management
- checkout: Checkout session operations
- balance: Balance, payouts, and transfers
- payment_methods: Payment method operations
- disputes: Dispute handling
"""

from app.connectors.stripe.balance import StripeBalanceMixin
from app.connectors.stripe.base import (
    StripeBase,
    build_stripe_kwargs,
    requires_stripe_config,
    requires_stripe_init,
)
from app.connectors.stripe.checkout import StripeCheckoutMixin
from app.connectors.stripe.coupons import StripeCouponsMixin
from app.connectors.stripe.customers import StripeCustomersMixin
from app.connectors.stripe.disputes import StripeDisputesMixin
from app.connectors.stripe.events import StripeEventsMixin
from app.connectors.stripe.invoices import StripeInvoicesMixin
from app.connectors.stripe.payment_methods import StripePaymentMethodsMixin
from app.connectors.stripe.payments import StripePaymentsMixin
from app.connectors.stripe.products import StripeProductsMixin
from app.connectors.stripe.subscriptions import StripeSubscriptionsMixin


class StripeConnector(
    StripeBase,
    StripePaymentsMixin,
    StripeCustomersMixin,
    StripeProductsMixin,
    StripeInvoicesMixin,
    StripeSubscriptionsMixin,
    StripeCheckoutMixin,
    StripeBalanceMixin,
    StripePaymentMethodsMixin,
    StripeDisputesMixin,
    StripeCouponsMixin,
    StripeEventsMixin,
):
    """
    Stripe API connector.

    This class combines all Stripe operations through mixin classes:
    - Initialization (from StripeBase)
    - Payment intents and refunds (from StripePaymentsMixin)
    - Customer management (from StripeCustomersMixin)
    - Products and prices (from StripeProductsMixin)
    - Invoice operations (from StripeInvoicesMixin)
    - Subscription management (from StripeSubscriptionsMixin)
    - Checkout sessions (from StripeCheckoutMixin)
    - Balance and payouts (from StripeBalanceMixin)
    - Payment methods (from StripePaymentMethodsMixin)
    - Dispute handling (from StripeDisputesMixin)
    """

    pass


__all__ = [
    "StripeConnector",
    "build_stripe_kwargs",
    "requires_stripe_config",
    "requires_stripe_init",
]
