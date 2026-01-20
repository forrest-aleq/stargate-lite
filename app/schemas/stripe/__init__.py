"""
Stripe Capability Schemas.

Aggregates all Stripe capability schemas from submodules.
"""

from app.schemas.base import CapabilitySchema
from app.schemas.stripe.accounts import ACCOUNT_SCHEMAS
from app.schemas.stripe.billing import BILLING_SCHEMAS
from app.schemas.stripe.billing_portal import BILLING_PORTAL_SCHEMAS
from app.schemas.stripe.checkout import CHECKOUT_SCHEMAS
from app.schemas.stripe.connect import CONNECT_SCHEMAS
from app.schemas.stripe.coupons import COUPON_SCHEMAS
from app.schemas.stripe.credit_notes import CREDIT_NOTE_SCHEMAS
from app.schemas.stripe.customers import CUSTOMER_SCHEMAS
from app.schemas.stripe.files import FILE_SCHEMAS
from app.schemas.stripe.financial_connections import FINANCIAL_CONNECTIONS_SCHEMAS
from app.schemas.stripe.identity import IDENTITY_SCHEMAS
from app.schemas.stripe.invoices import INVOICE_SCHEMAS
from app.schemas.stripe.issuing_cards import ISSUING_CARD_SCHEMAS
from app.schemas.stripe.issuing_disputes import ISSUING_DISPUTE_SCHEMAS
from app.schemas.stripe.issuing_transactions import ISSUING_TRANSACTION_SCHEMAS
from app.schemas.stripe.outbound_transfers import OUTBOUND_TRANSFER_SCHEMAS
from app.schemas.stripe.payment_links import PAYMENT_LINK_SCHEMAS
from app.schemas.stripe.payments import PAYMENT_SCHEMAS
from app.schemas.stripe.prices import PRICE_SCHEMAS
from app.schemas.stripe.products import PRODUCT_SCHEMAS
from app.schemas.stripe.quotes import QUOTE_SCHEMAS
from app.schemas.stripe.radar import RADAR_SCHEMAS
from app.schemas.stripe.setup_intents import SETUP_INTENT_SCHEMAS
from app.schemas.stripe.subscriptions import SUBSCRIPTION_SCHEMAS
from app.schemas.stripe.tax import TAX_SCHEMAS
from app.schemas.stripe.tax_settings import TAX_SETTINGS_SCHEMAS
from app.schemas.stripe.terminal import TERMINAL_SCHEMAS
from app.schemas.stripe.terminal_locations import TERMINAL_LOCATION_SCHEMAS
from app.schemas.stripe.treasury import TREASURY_SCHEMAS
from app.schemas.stripe.value_lists import VALUE_LIST_SCHEMAS
from app.schemas.stripe.webhooks import WEBHOOK_SCHEMAS

# Aggregate all Stripe schemas
STRIPE_SCHEMAS: dict[str, CapabilitySchema] = {
    **PAYMENT_SCHEMAS,
    **CUSTOMER_SCHEMAS,
    **PRODUCT_SCHEMAS,
    **PRICE_SCHEMAS,
    **SUBSCRIPTION_SCHEMAS,
    **INVOICE_SCHEMAS,
    **CHECKOUT_SCHEMAS,
    **BILLING_SCHEMAS,
    **CONNECT_SCHEMAS,
    **WEBHOOK_SCHEMAS,
    **TERMINAL_SCHEMAS,
    **TERMINAL_LOCATION_SCHEMAS,
    **ISSUING_CARD_SCHEMAS,
    **ISSUING_TRANSACTION_SCHEMAS,
    **ISSUING_DISPUTE_SCHEMAS,
    **TREASURY_SCHEMAS,
    **OUTBOUND_TRANSFER_SCHEMAS,
    **IDENTITY_SCHEMAS,
    **RADAR_SCHEMAS,
    **VALUE_LIST_SCHEMAS,
    **TAX_SCHEMAS,
    **TAX_SETTINGS_SCHEMAS,
    **COUPON_SCHEMAS,
    **SETUP_INTENT_SCHEMAS,
    **PAYMENT_LINK_SCHEMAS,
    **QUOTE_SCHEMAS,
    **CREDIT_NOTE_SCHEMAS,
    **BILLING_PORTAL_SCHEMAS,
    **FINANCIAL_CONNECTIONS_SCHEMAS,
    **FILE_SCHEMAS,
    **ACCOUNT_SCHEMAS,
}

__all__ = ["STRIPE_SCHEMAS"]
