"""
ClickUp API Connector

Enables Aleq to manage tasks, lists, and projects in ClickUp workspaces.
Finance teams use ClickUp for process management, approvals, and workflows.

API Documentation: https://developer.clickup.com/
Base URL: https://api.clickup.com/api/v2
"""

from .lists_spaces import ListsSpacesMixin


class ClickUpConnector(ListsSpacesMixin):
    """
    ClickUp API connector for task and project management.

    Inherits from ListsSpacesMixin which inherits from TasksMixin
    which inherits from ClickUpBase.

    ClickUp is used by finance teams for:
    - Invoice approval workflows
    - Month-end close checklists
    - Budget review processes
    - Cross-functional project tracking
    """

    pass


__all__ = ["ClickUpConnector"]
