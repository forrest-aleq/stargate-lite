"""
Stripe connector - Base module

Base class with initialization and configuration.
"""

import os

import stripe

from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeBase:
    """Base Stripe connector with initialization"""

    def __init__(self) -> None:
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is required but not set")
        stripe.api_key = self.api_key
