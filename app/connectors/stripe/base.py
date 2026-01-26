"""
Stripe connector - Base module

Base class with initialization and configuration.
"""

import os

import stripe

from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeBase:
    """Base Stripe connector with lazy initialization"""

    _initialized: bool = False

    def __init__(self) -> None:
        # Lazy init - don't fail at import time if key is missing
        self.api_key: str | None = None

    def _ensure_initialized(self) -> None:
        """Initialize Stripe API key on first use"""
        if self._initialized:
            return
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            from app.errors import CredentialMissingError
            raise CredentialMissingError("stripe", "SYSTEM", "AGENT")
        stripe.api_key = self.api_key
        self._initialized = True
