"""
Stripe connector - Base module

Base class with initialization and configuration.
Supports both:
1. Per-customer OAuth via Stripe Connect (connected accounts)
2. Fallback to platform STRIPE_SECRET_KEY (legacy mode)

Uses lazy initialization - won't fail at import/instantiation if STRIPE_SECRET_KEY is missing.
Only fails when an actual Stripe API method is called.
"""

import os
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import stripe

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def requires_stripe_init(method: F) -> F:
    """
    Decorator that ensures Stripe API key is initialized before method execution.

    DEPRECATED: Use @requires_stripe_config instead for connected account support.

    Usage:
        @requires_stripe_init
        def create_customer(self, org_id: str, user_id: str, args: dict) -> dict:
            ...
    """

    @wraps(method)
    def wrapper(self: "StripeBase", *args: Any, **kwargs: Any) -> Any:
        self._ensure_initialized()
        return method(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


def requires_stripe_config(method: F) -> F:
    """
    Decorator that retrieves Stripe config (connected account or platform) before method execution.

    This decorator:
    1. Ensures the platform Stripe API key is initialized
    2. Retrieves per-customer credential if available
    3. Injects stripe_config dict into the method kwargs

    Usage:
        @requires_stripe_config
        def create_customer(self, org_id: str, user_id: str, args: dict,
                           stripe_config: dict | None = None) -> dict:
            # stripe_config contains: {"stripe_account": "acct_xxx", "is_connected_account": True}
            # or: {"stripe_account": None, "is_connected_account": False} for platform
            ...
    """

    @wraps(method)
    def wrapper(self: "StripeBase", org_id: str, user_id: str, *args: Any, **kwargs: Any) -> Any:
        self._ensure_initialized()
        stripe_config = self._get_stripe_config(org_id, user_id)
        kwargs["stripe_config"] = stripe_config
        return method(self, org_id, user_id, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


class StripeBase:
    """
    Base Stripe connector with lazy initialization.

    Supports two modes of operation:
    1. Connected Account (via Stripe Connect OAuth):
       - Customer connects their Stripe account
       - API calls include stripe_account parameter
       - Operations happen on customer's Stripe account

    2. Platform Account (legacy):
       - Uses global STRIPE_SECRET_KEY
       - API calls use platform account
       - Falls back to this if no customer credential exists
    """

    _initialized: bool = False

    def __init__(self) -> None:
        # Lazy init - don't fail at import time if key is missing
        self.api_key: str | None = None

    def _ensure_initialized(self) -> None:
        """Initialize Stripe API key on first use"""
        if StripeBase._initialized:
            return

        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            from app.errors import CredentialMissingError

            raise CredentialMissingError("stripe", "SYSTEM", "AGENT")

        stripe.api_key = self.api_key
        StripeBase._initialized = True
        logger.info(
            "Stripe API initialized",
            service="stripe",
            log_event="stripe_init_success",
        )

    def _get_stripe_config(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get Stripe config - tries per-customer credential first, falls back to platform.

        Args:
            org_id: Organization ID
            user_id: User ID

        Returns:
            Dict with:
            - stripe_account: Connected account ID (e.g., "acct_xxx") or None for platform
            - is_connected_account: True if using a connected account
        """
        # Try to get per-customer credential
        cred = CredentialManager.get_credential(org_id, user_id, "stripe", "customer")

        if cred and cred.get("extra_data", {}).get("stripe_user_id"):
            stripe_user_id = cred["extra_data"]["stripe_user_id"]
            logger.debug(
                "Using connected Stripe account",
                service="stripe",
                org_id=org_id,
                user_id=user_id,
                stripe_account=stripe_user_id,
                log_event="stripe_connected_account",
            )
            return {
                "stripe_account": stripe_user_id,
                "is_connected_account": True,
            }

        # Fallback to platform key
        logger.debug(
            "Using platform Stripe account (no connected account found)",
            service="stripe",
            org_id=org_id,
            user_id=user_id,
            log_event="stripe_platform_account",
        )
        return {
            "stripe_account": None,
            "is_connected_account": False,
        }


def build_stripe_kwargs(
    stripe_config: dict[str, Any] | None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Helper to build Stripe API kwargs with optional stripe_account parameter.

    Args:
        stripe_config: Config dict from _get_stripe_config (or None)
        **kwargs: Base API parameters

    Returns:
        Dict with kwargs, plus stripe_account if using connected account
    """
    result = dict(kwargs)
    if stripe_config and stripe_config.get("stripe_account"):
        result["stripe_account"] = stripe_config["stripe_account"]
    return result
