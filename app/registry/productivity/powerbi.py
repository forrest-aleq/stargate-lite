"""
Power BI Capability Registry
"""

from app.connectors.powerbi import PowerBIConnector

# Initialize connector
powerbi_connector = PowerBIConnector()

DELEGATION_INSTRUCTIONS = "Grant Aleq access to your Power BI workspace"

POWERBI_CAPABILITIES = {
    # ========== POWER BI ==========
    "powerbi.dataset.list": {
        "handler": powerbi_connector.list_datasets,
        "tool_name": "powerbi.list_datasets",
        "description": "List datasets in workspace",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.dataset.get": {
        "handler": powerbi_connector.get_dataset,
        "tool_name": "powerbi.get_dataset",
        "description": "Get dataset details",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.dataset.refresh": {
        "handler": powerbi_connector.refresh_dataset,
        "tool_name": "powerbi.refresh_dataset",
        "description": "Trigger dataset refresh",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.report.list": {
        "handler": powerbi_connector.list_reports,
        "tool_name": "powerbi.list_reports",
        "description": "List reports in workspace",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.report.get": {
        "handler": powerbi_connector.get_report,
        "tool_name": "powerbi.get_report",
        "description": "Get report details",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.report.export": {
        "handler": powerbi_connector.export_report,
        "tool_name": "powerbi.export_report",
        "description": "Export report to file (PDF/PPTX/PNG)",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.dashboard.list": {
        "handler": powerbi_connector.list_dashboards,
        "tool_name": "powerbi.list_dashboards",
        "description": "List dashboards in workspace",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.dashboard.get": {
        "handler": powerbi_connector.get_dashboard,
        "tool_name": "powerbi.get_dashboard",
        "description": "Get dashboard details",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.embedtoken.generate": {
        "handler": powerbi_connector.generate_embed_token,
        "tool_name": "powerbi.generate_embed_token",
        "description": "Generate embed token for reports/dashboards",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
    "powerbi.workspace.create": {
        "handler": powerbi_connector.create_workspace,
        "tool_name": "powerbi.create_workspace",
        "description": "Create new workspace (group)",
        "requires_oauth": True,
        "service": "powerbi",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": DELEGATION_INSTRUCTIONS,
    },
}
