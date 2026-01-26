"""
Stripe connector - Base module

Base class with initialization and configuration.
Uses lazy initialization - won't fail at import/instantiation if STRIPE_SECRET_KEY is missing.
Only fails when an actual Stripe API method is called.
"""

import os
from functools import wraps
from typing import Any, Callable, TypeVar

import stripe

from app.logging_config import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def requires_stripe_init(method: F) -> F:
    """
    Decorator that ensures Stripe API key is initialized before method execution.

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


class StripeBase:
    """
    Base Stripe connector with lazy initialization.

    Stripe uses a global API key (not per-customer OAuth), so we:
    1. Don't fail at import/instantiation time if key is missing
    2. Only initialize when an actual API method is called
    3. Use @requires_stripe_init decorator on all mixin methods
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
