"""
Gmail connector for Stargate Lite
Handles OAuth 2.0 and email operations
"""

from .read import ReadMixin


class GmailConnector(ReadMixin):
    """
    Gmail API connector.

    Inherits from ReadMixin which inherits from SendMixin
    which inherits from GmailBase.
    """

    pass


__all__ = ["GmailConnector"]
