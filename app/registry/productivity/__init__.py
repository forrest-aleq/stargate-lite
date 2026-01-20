"""
Productivity/BI Capability Registry Package

Aggregates capabilities from:
- HubSpot (CRM)
- Notion (docs/databases)
- Asana (project management)
- Linear (issue tracking)
- ClickUp (project management)
- Monday.com (work OS)
- Power BI (business intelligence)
- DocuSign (eSignature)
- Airtable (databases)
"""

from app.registry.productivity.airtable import AIRTABLE_CAPABILITIES
from app.registry.productivity.asana import ASANA_CAPABILITIES
from app.registry.productivity.clickup import CLICKUP_CAPABILITIES
from app.registry.productivity.docusign import DOCUSIGN_CAPABILITIES
from app.registry.productivity.hubspot import HUBSPOT_CAPABILITIES
from app.registry.productivity.linear import LINEAR_CAPABILITIES
from app.registry.productivity.monday import MONDAY_CAPABILITIES
from app.registry.productivity.notion import NOTION_CAPABILITIES
from app.registry.productivity.powerbi import POWERBI_CAPABILITIES

# Aggregate all productivity capabilities
PRODUCTIVITY_CAPABILITIES = {
    **HUBSPOT_CAPABILITIES,
    **NOTION_CAPABILITIES,
    **ASANA_CAPABILITIES,
    **LINEAR_CAPABILITIES,
    **CLICKUP_CAPABILITIES,
    **MONDAY_CAPABILITIES,
    **POWERBI_CAPABILITIES,
    **DOCUSIGN_CAPABILITIES,
    **AIRTABLE_CAPABILITIES,
}

__all__ = ["PRODUCTIVITY_CAPABILITIES"]
