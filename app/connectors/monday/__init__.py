"""
Monday.com API Connector

Enables Aleq to manage boards, items, and workflows in Monday.com workspaces.
Finance and operations teams use Monday.com for task management and process tracking.

API Documentation: https://developer.monday.com/api-reference/
Base URL: https://api.monday.com/v2 (GraphQL)
"""

from .users import UsersMixin


class MondayConnector(UsersMixin):
    """
    Monday.com GraphQL API connector for task and workflow management.

    Inherits from UsersMixin which inherits from ItemsMixin
    which inherits from BoardsMixin which inherits from MondayBase.

    Monday.com is used by finance/operations teams for:
    - Invoice approval workflows
    - Month-end close tracking
    - Budget review boards
    - Cross-functional project coordination
    """

    pass


__all__ = ["MondayConnector"]
