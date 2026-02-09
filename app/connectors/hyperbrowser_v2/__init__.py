"""
Hyperbrowser Connector v2 - Cloud Browser Automation
Using Hyperbrowser's managed Claude Computer Use agent (February 2026)

ARCHITECTURE:
This connector delegates browser automation to Hyperbrowser's cloud service.
Hyperbrowser runs isolated browser containers and manages the full
screenshot→Claude→action→screenshot loop via their managed agent API.

INTEGRATION POINTS:
1. Hyperbrowser Cloud API - For managed browser sessions and agent execution
2. CredentialManager - For portal credentials
3. File Storage - For downloaded files (via Hyperbrowser downloads API)

EXECUTION FLOW:
1. Send natural language goal to Hyperbrowser's Claude Computer Use agent
2. Hyperbrowser spins up isolated browser container
3. Managed agent handles screenshot→Claude→action loop internally
4. Returns final result and status when goal is achieved or max steps reached
"""

from .environment import HyperbrowserCloud
from .workflows import WorkflowsMixin


class HyperbrowserConnectorV2(WorkflowsMixin):
    """
    Cloud browser automation connector using Hyperbrowser.

    Inherits from WorkflowsMixin which inherits from BrowserActionsMixin
    which inherits from HyperbrowserBase.

    REQUIREMENTS:
    - HYPERBROWSER_API_KEY in environment
    - Optional: Credentials in CredentialManager for portal logins
    """

    pass


__all__ = ["HyperbrowserCloud", "HyperbrowserConnectorV2"]
