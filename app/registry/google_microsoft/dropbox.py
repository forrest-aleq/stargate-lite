"""
Dropbox Capability Registry
"""

from app.connectors.dropbox import DropboxConnector

# Initialize connector
dropbox_connector = DropboxConnector()

DROPBOX_CAPABILITIES = {
    # ========== DROPBOX ==========
    "dropbox.file.upload": {
        "handler": dropbox_connector.upload_file,
        "tool_name": "dropbox.upload_file",
        "description": "Upload file to Dropbox",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
    "dropbox.file.download": {
        "handler": dropbox_connector.download_file,
        "tool_name": "dropbox.download_file",
        "description": "Download file from Dropbox",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
    "dropbox.file.list": {
        "handler": dropbox_connector.list_files,
        "tool_name": "dropbox.list_files",
        "description": "List files in Dropbox folder",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
    "dropbox.folder.create": {
        "handler": dropbox_connector.create_folder,
        "tool_name": "dropbox.create_folder",
        "description": "Create folder in Dropbox",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
    "dropbox.file.metadata": {
        "handler": dropbox_connector.get_file_metadata,
        "tool_name": "dropbox.get_file_metadata",
        "description": "Get file metadata from Dropbox",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
    "dropbox.file.delete": {
        "handler": dropbox_connector.delete_file,
        "tool_name": "dropbox.delete_file",
        "description": "Delete file from Dropbox",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
    "dropbox.file.move": {
        "handler": dropbox_connector.move_file,
        "tool_name": "dropbox.move_file",
        "description": "Move or rename file in Dropbox",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
    "dropbox.file.search": {
        "handler": dropbox_connector.search_files,
        "tool_name": "dropbox.search_files",
        "description": "Search for files in Dropbox",
        "requires_oauth": True,
        "service": "dropbox",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Grant Aleq access to your Dropbox",
    },
}
