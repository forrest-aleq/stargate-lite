"""
Linear connector for Stargate Lite
Optimized for Linear Agents (actor=app mode)
Supports agent identity, @mentions, and issue assignments
Uses Linear GraphQL API (2025)
"""

from .teams import TeamsMixin


class LinearConnector(TeamsMixin):
    """
    Linear API connector with agent capabilities.

    Inherits from TeamsMixin which inherits from IssuesMixin
    which inherits from LinearBase.

    Linear agents can:
    - Be assigned issues (app:assignable scope)
    - Be @mentioned in comments (app:mentionable scope)
    - Create issues/comments with custom identity
    - Participate as first-class team members
    """

    pass


__all__ = ["LinearConnector"]
