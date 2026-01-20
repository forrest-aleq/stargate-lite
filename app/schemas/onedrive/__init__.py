"""
Microsoft OneDrive Capability Schemas.

Rich metadata for file upload, download, and management via Microsoft Graph API.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ FILE UPLOAD ============

ONEDRIVE_FILE_UPLOAD = CapabilitySchema(
    capability_key="onedrive.file.upload",
    service="microsoft",
    category="files",
    description="Upload file to OneDrive",
    description_detailed=(
        "Uploads a file to OneDrive. File content must be base64 encoded. "
        "Optionally specify a folder path to upload into a specific folder."
    ),
    parameters={
        "file_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the uploaded file",
            example="report.pdf",
        ),
        "file_content": ParameterSchema(
            type="string",
            required=True,
            description="Base64 encoded file content",
        ),
        "folder_path": ParameterSchema(
            type="string",
            required=False,
            description="Folder path (e.g., '/Documents'). Uploads to root if omitted",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="OneDrive file ID"),
        "file_name": ReturnFieldSchema(type="string", description="Uploaded file name"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size in bytes"),
        "created_time": ReturnFieldSchema(type="string", description="Creation timestamp"),
        "web_url": ReturnFieldSchema(type="string", description="URL to view file"),
        "status": ReturnFieldSchema(type="string", description="Should be 'uploaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid file content or folder path",
            recovery_hint="Ensure file_content is valid base64 and folder exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["onedrive.file.metadata"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ FILE DOWNLOAD ============

ONEDRIVE_FILE_DOWNLOAD = CapabilitySchema(
    capability_key="onedrive.file.download",
    service="microsoft",
    category="files",
    description="Download file from OneDrive",
    description_detailed=(
        "Downloads a file from OneDrive by its file ID. "
        "Returns the file content as base64 encoded string."
    ),
    parameters={
        "file_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive file ID",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="File ID"),
        "file_name": ReturnFieldSchema(type="string", description="File name"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size"),
        "file_content": ReturnFieldSchema(type="string", description="Base64 encoded content"),
        "status": ReturnFieldSchema(type="string", description="Should be 'downloaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="File not found",
            recovery_hint="Verify file_id exists using onedrive.file.list",
        ),
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["onedrive.file.list", "onedrive.file.metadata"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ FILE LIST ============

ONEDRIVE_FILE_LIST = CapabilitySchema(
    capability_key="onedrive.file.list",
    service="microsoft",
    category="files",
    description="List files in OneDrive",
    description_detailed=(
        "Lists files in OneDrive, optionally filtered by folder ID or path. "
        "Returns file metadata including IDs, names, sizes, and folder indicators."
    ),
    parameters={
        "folder_id": ParameterSchema(
            type="string",
            required=False,
            description="List files in specific folder by ID",
        ),
        "folder_path": ParameterSchema(
            type="string",
            required=False,
            description="List files in specific folder by path (e.g., '/Documents')",
        ),
    },
    returns={
        "files": ReturnFieldSchema(
            type="array",
            description="List of file objects with id, name, size, is_folder, timestamps",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of files returned"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["onedrive.file.download", "onedrive.file.metadata"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ FOLDER CREATE ============

ONEDRIVE_FOLDER_CREATE = CapabilitySchema(
    capability_key="onedrive.folder.create",
    service="microsoft",
    category="files",
    description="Create a folder in OneDrive",
    description_detailed=(
        "Creates a new folder in OneDrive. Can be created at root level "
        "or as a subfolder using parent folder ID or path."
    ),
    parameters={
        "folder_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the new folder",
            example="Project Documents",
        ),
        "parent_folder_id": ParameterSchema(
            type="string",
            required=False,
            description="Parent folder ID",
        ),
        "parent_folder_path": ParameterSchema(
            type="string",
            required=False,
            description="Parent folder path (e.g., '/Documents')",
        ),
    },
    returns={
        "folder_id": ReturnFieldSchema(type="string", description="New folder ID"),
        "folder_name": ReturnFieldSchema(type="string", description="Folder name"),
        "web_url": ReturnFieldSchema(type="string", description="URL to view folder"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["onedrive.file.upload"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ FILE METADATA ============

ONEDRIVE_FILE_METADATA = CapabilitySchema(
    capability_key="onedrive.file.metadata",
    service="microsoft",
    category="files",
    description="Get file metadata without downloading content",
    description_detailed=(
        "Retrieves detailed metadata for a file including name, size, type, "
        "timestamps, and whether it's a folder. Does not download the file content."
    ),
    parameters={
        "file_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive file ID",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="File ID"),
        "file_name": ReturnFieldSchema(type="string", description="File name"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size"),
        "is_folder": ReturnFieldSchema(type="boolean", description="Whether item is a folder"),
        "created_time": ReturnFieldSchema(type="string", description="Creation time"),
        "modified_time": ReturnFieldSchema(type="string", description="Last modified time"),
        "web_url": ReturnFieldSchema(type="string", description="View URL"),
        "mime_type": ReturnFieldSchema(type="string", description="MIME type (files only)"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="File not found",
            recovery_hint="Verify file_id exists using onedrive.file.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["onedrive.file.list"],
        typically_followed_by=["onedrive.file.download"],
    ),
    idempotent=True,
    has_side_effects=False,
)

ONEDRIVE_SCHEMAS: dict[str, CapabilitySchema] = {
    "onedrive.file.upload": ONEDRIVE_FILE_UPLOAD,
    "onedrive.file.download": ONEDRIVE_FILE_DOWNLOAD,
    "onedrive.file.list": ONEDRIVE_FILE_LIST,
    "onedrive.folder.create": ONEDRIVE_FOLDER_CREATE,
    "onedrive.file.metadata": ONEDRIVE_FILE_METADATA,
}

__all__ = ["ONEDRIVE_SCHEMAS"]
