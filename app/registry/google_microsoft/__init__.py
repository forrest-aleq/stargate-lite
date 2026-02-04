"""
Google Workspace & Microsoft 365 & Dropbox Capability Registry (package)
"""

from app.registry.google_microsoft.dropbox import DROPBOX_CAPABILITIES
from app.registry.google_microsoft.google import GOOGLE_CAPABILITIES
from app.registry.google_microsoft.microsoft import MICROSOFT_CAPABILITIES

GOOGLE_MICROSOFT_CAPABILITIES = {
    **GOOGLE_CAPABILITIES,
    **MICROSOFT_CAPABILITIES,
    **DROPBOX_CAPABILITIES,
}
