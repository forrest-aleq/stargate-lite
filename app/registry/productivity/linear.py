"""
Linear Capability Registry
"""

from app.connectors.linear import LinearConnector

# Initialize connector
linear_connector = LinearConnector()

DELEGATION_INSTRUCTIONS = "Install Aleq agent in your Linear workspace"

LINEAR_CAPABILITIES = {
    # ========== LINEAR ==========
    "linear.issue.create": {
        "handler": linear_connector.create_issue,
        "tool_name": "linear.create_issue",
        "description": (
            "Create issue in Linear as Aleq AI agent - supports @mentions and assignments"
        ),
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Install Aleq agent in your Linear workspace - "
            "agent can be assigned issues and @mentioned"
        ),
    },
    "linear.issue.update": {
        "handler": linear_connector.update_issue,
        "tool_name": "linear.update_issue",
        "description": "Update issue in Linear",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.issue.get": {
        "handler": linear_connector.get_issue,
        "tool_name": "linear.get_issue",
        "description": "Get issue details from Linear",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.issue.list": {
        "handler": linear_connector.list_issues,
        "tool_name": "linear.list_issues",
        "description": "List issues in Linear with filtering",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.comment.create": {
        "handler": linear_connector.create_comment,
        "tool_name": "linear.create_comment",
        "description": "Comment on Linear issue as Aleq AI agent",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.team.list": {
        "handler": linear_connector.list_teams,
        "tool_name": "linear.list_teams",
        "description": "List teams in Linear workspace",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.team.get": {
        "handler": linear_connector.get_team,
        "tool_name": "linear.get_team",
        "description": "Get team details from Linear",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.project.list": {
        "handler": linear_connector.list_projects,
        "tool_name": "linear.list_projects",
        "description": "List projects in Linear workspace",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.label.create": {
        "handler": linear_connector.create_label,
        "tool_name": "linear.create_label",
        "description": "Create label in Linear",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "linear.agent.viewer": {
        "handler": linear_connector.get_viewer,
        "tool_name": "linear.get_viewer",
        "description": "Get current Linear agent user info (for debugging)",
        "requires_oauth": True,
        "service": "linear",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
}
