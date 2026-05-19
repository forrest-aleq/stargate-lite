"""
Stripe connector - Coupons module

Handles coupon CRUD operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_config
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeCouponsMixin:
    """Stripe coupon operations mixin"""

    @requires_stripe_config
    def create_coupon(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a coupon"""
        percent_off = args.get("percent_off")
        amount_off = args.get("amount_off")
        currency = args.get("currency", "usd")
        duration = args.get("duration", "once")
        duration_in_months = args.get("duration_in_months")
        name = args.get("name")
        max_redemptions = args.get("max_redemptions")
        metadata = args.get("metadata", {})

        logger.info(
            "Creating coupon",
            service="stripe",
            duration=duration,
            log_event="stripe_coupon_create",
        )

        create_kwargs: dict[str, Any] = {
            "duration": duration,
            "metadata": metadata,
        }
        if percent_off is not None:
            create_kwargs["percent_off"] = percent_off
        if amount_off is not None:
            create_kwargs["amount_off"] = amount_off
            create_kwargs["currency"] = currency
        if duration_in_months:
            create_kwargs["duration_in_months"] = duration_in_months
        if name:
            create_kwargs["name"] = name
        if max_redemptions:
            create_kwargs["max_redemptions"] = max_redemptions
        if stripe_config and stripe_config.get("stripe_account"):
            create_kwargs["stripe_account"] = stripe_config["stripe_account"]

        coupon = stripe.Coupon.create(**create_kwargs)

        logger.info(
            "Coupon created",
            service="stripe",
            coupon_id=coupon.id,
            log_event="stripe_coupon_created",
        )

        return {
            "coupon_id": coupon.id,
            "name": coupon.name,
            "percent_off": coupon.percent_off,
            "amount_off": coupon.amount_off,
            "currency": coupon.currency,
            "duration": coupon.duration,
            "valid": coupon.valid,
        }

    @requires_stripe_config
    def retrieve_coupon(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a coupon"""
        coupon_id = args.get("coupon_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        coupon = stripe.Coupon.retrieve(coupon_id, **retrieve_kwargs)
        return {
            "coupon_id": coupon.id,
            "name": coupon.name,
            "percent_off": coupon.percent_off,
            "amount_off": coupon.amount_off,
            "currency": coupon.currency,
            "duration": coupon.duration,
            "valid": coupon.valid,
            "times_redeemed": coupon.times_redeemed,
            "max_redemptions": coupon.max_redemptions,
        }

    @requires_stripe_config
    def list_coupons(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List coupons"""
        limit = args.get("limit", 10)

        params: dict[str, Any] = {"limit": limit}
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

        coupons = stripe.Coupon.list(**params)
        return {
            "coupons": [
                {
                    "coupon_id": c.id,
                    "name": c.name,
                    "percent_off": c.percent_off,
                    "amount_off": c.amount_off,
                    "duration": c.duration,
                    "valid": c.valid,
                }
                for c in coupons.data
            ],
            "has_more": coupons.has_more,
        }

    @requires_stripe_config
    def delete_coupon(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Delete a coupon"""
        coupon_id = args.get("coupon_id")

        delete_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            delete_kwargs["stripe_account"] = stripe_config["stripe_account"]

        deleted = stripe.Coupon.delete(coupon_id, **delete_kwargs)
        return {"coupon_id": deleted.id, "deleted": deleted.deleted}
