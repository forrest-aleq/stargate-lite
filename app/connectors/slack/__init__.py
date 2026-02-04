"""
Slack connector for Stargate Lite.

Handles OAuth 2.0 and messaging, channel, and user operations.
"""

from .channels import ChannelsMixin


class SlackConnector(ChannelsMixin):
    """Slack API connector with full capability coverage."""

    pass


__all__ = ["SlackConnector"]
