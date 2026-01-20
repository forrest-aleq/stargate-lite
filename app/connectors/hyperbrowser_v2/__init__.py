"""
Hyperbrowser Connector v2 - Production-Ready Browser Automation
Using Anthropic's Computer Use API (October 2025)

ARCHITECTURE:
This connector provides the API layer for browser automation.
It requires an execution environment (Docker container, VM, or cloud service)
that runs a real browser and executes the computer use actions.

INTEGRATION POINTS:
1. Anthropic Computer Use API - For action decisions
2. Execution Environment - For action execution (separate service)
3. CredentialManager - For portal credentials
4. File Storage - For downloaded files

EXECUTION FLOW:
1. Take screenshot of current browser state
2. Send screenshot + goal to Claude
3. Claude analyzes and decides action (click, type, etc.)
4. Execute action in real browser environment
5. Get result (success/failure, new screenshot)
6. Feed result back to Claude
7. Repeat until goal achieved or max iterations
"""

from .environment import BrowserExecutionEnvironment
from .workflows import WorkflowsMixin


class HyperbrowserConnectorV2(WorkflowsMixin):
    """
    Production-ready browser automation connector.

    Inherits from WorkflowsMixin which inherits from BrowserActionsMixin
    which inherits from HyperbrowserBase.

    REQUIREMENTS:
    - ANTHROPIC_API_KEY in environment
    - Execution environment (Docker/VM/cloud service)
    - Optional: Credentials in CredentialManager for portal logins
    """

    pass


__all__ = ["BrowserExecutionEnvironment", "HyperbrowserConnectorV2"]
