"""
Notion Capability Registry
"""

from app.connectors.notion import NotionConnector

# Initialize connector
notion_connector = NotionConnector()

NOTION_CAPABILITIES = {
    # ========== NOTION ==========
    "notion.database.query": {
        "handler": notion_connector.query_database,
        "tool_name": "notion.query_database",
        "description": "Query a Notion database (API 2025-09-03)",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.page.create": {
        "handler": notion_connector.create_page,
        "tool_name": "notion.create_page",
        "description": "Create page in database (uses data_source_id)",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.page.update": {
        "handler": notion_connector.update_page,
        "tool_name": "notion.update_page",
        "description": "Update page properties",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.page.get": {
        "handler": notion_connector.get_page,
        "tool_name": "notion.get_page",
        "description": "Get page details",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.block.append": {
        "handler": notion_connector.append_block_children,
        "tool_name": "notion.append_block_children",
        "description": "Append blocks to page (max 100)",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.block.children.get": {
        "handler": notion_connector.get_block_children,
        "tool_name": "notion.get_block_children",
        "description": "Get children of a block",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.database.get": {
        "handler": notion_connector.get_database,
        "tool_name": "notion.get_database",
        "description": "Get database details",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.datasource.get": {
        "handler": notion_connector.get_data_sources,
        "tool_name": "notion.get_data_sources",
        "description": "Get data sources for database (2025-09-03)",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.database.create": {
        "handler": notion_connector.create_database,
        "tool_name": "notion.create_database",
        "description": "Create a new database",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
    "notion.search": {
        "handler": notion_connector.search,
        "tool_name": "notion.search",
        "description": "Search Notion workspace",
        "requires_oauth": True,
        "service": "notion",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Notion workspace",
    },
}
