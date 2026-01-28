"""
ClickUp Capability Registry
"""

from app.connectors.clickup import ClickUpConnector

# Initialize connector
clickup_connector = ClickUpConnector()

DELEGATION_INSTRUCTIONS = "Connect your ClickUp workspace to Aleq"

CLICKUP_CAPABILITIES = {
    # ========== CLICKUP ==========
    "clickup.task.create": {
        "handler": clickup_connector.create_task,
        "tool_name": "clickup.create_task",
        "description": (
            "Create task in ClickUp for finance workflows (approvals, reviews, month-end)"
        ),
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.task.get": {
        "handler": clickup_connector.get_task,
        "tool_name": "clickup.get_task",
        "description": "Get task details from ClickUp",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.task.update": {
        "handler": clickup_connector.update_task,
        "tool_name": "clickup.update_task",
        "description": "Update task in ClickUp (status, assignees, priority)",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.task.list": {
        "handler": clickup_connector.list_tasks,
        "tool_name": "clickup.list_tasks",
        "description": "List tasks in ClickUp with filtering",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.list.get": {
        "handler": clickup_connector.get_list,
        "tool_name": "clickup.get_list",
        "description": "Get list details from ClickUp",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.list.get_in_folder": {
        "handler": clickup_connector.get_lists_in_folder,
        "tool_name": "clickup.get_lists_in_folder",
        "description": "Get all lists in a ClickUp folder",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.list.get_in_space": {
        "handler": clickup_connector.get_lists_in_space,
        "tool_name": "clickup.get_lists_in_space",
        "description": "Get folderless lists in a ClickUp space",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.space.list": {
        "handler": clickup_connector.get_spaces,
        "tool_name": "clickup.get_spaces",
        "description": "List spaces in ClickUp workspace",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.space.get": {
        "handler": clickup_connector.get_space,
        "tool_name": "clickup.get_space",
        "description": "Get space details from ClickUp",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.comment.create": {
        "handler": clickup_connector.create_comment,
        "tool_name": "clickup.create_comment",
        "description": "Create comment on ClickUp task",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.comment.list": {
        "handler": clickup_connector.get_task_comments,
        "tool_name": "clickup.get_task_comments",
        "description": "Get all comments on ClickUp task",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "clickup.team.list": {
        "handler": clickup_connector.get_authorized_teams,
        "tool_name": "clickup.get_authorized_teams",
        "description": "Get all ClickUp workspaces user has access to",
        "requires_oauth": True,
        "service": "clickup",
        "credential_type": "customer",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
}
