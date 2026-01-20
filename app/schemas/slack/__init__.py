"""
Slack Capability Schemas.

Rich metadata for Slack messaging and channel operations.
"""

from app.schemas.base import CapabilitySchema

from .channels import SLACK_CHANNEL_SCHEMAS
from .extended import SLACK_EXTENDED_SCHEMAS
from .messaging import SLACK_MESSAGING_SCHEMAS

SLACK_SCHEMAS: dict[str, CapabilitySchema] = {
    **SLACK_MESSAGING_SCHEMAS,
    **SLACK_CHANNEL_SCHEMAS,
    **SLACK_EXTENDED_SCHEMAS,
}

__all__ = ["SLACK_SCHEMAS"]
