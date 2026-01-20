"""
Dropbox Capability Schemas.

Rich metadata for file upload, download, and management via Dropbox API v2.
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

DROPBOX_FILE_UPLOAD = CapabilitySchema(
    capability_key="dropbox.file.upload",
    service="dropbox",
    category="files",
    description="Upload file to Dropbox",
    description_detailed=(
        "Uploads a file to Dropbox. File content must be base64 encoded. "
        "Optionally specify a folder path to upload into a specific folder. "
        "Files are automatically renamed if a file with the same name exists."
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
        "file_id": ReturnFieldSchema(type="string", description="Dropbox file ID"),
        "file_name": ReturnFieldSchema(type="string", description="Uploaded file name"),
        "path": ReturnFieldSchema(type="string", description="Full file path"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size in bytes"),
        "modified_time": ReturnFieldSchema(type="string", description="Server modified timestamp"),
        "status": ReturnFieldSchema(type="string", description="Should be 'uploaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Dropbox OAuth credentials not configured",
            recovery_hint="User must complete Dropbox OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid file content or folder path",
            recovery_hint="Ensure file_content is valid base64 and folder exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["dropbox.file.metadata"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ FILE DOWNLOAD ============

DROPBOX_FILE_DOWNLOAD = CapabilitySchema(
    capability_key="dropbox.file.download",
    service="dropbox",
    category="files",
    description="Download file from Dropbox",
    description_detailed=(
        "Downloads a file from Dropbox by path or file ID. "
        "Returns the file content as base64 encoded string."
    ),
    parameters={
        "path": ParameterSchema(
            type="string",
            required=False,
            description="File path (e.g., '/Documents/report.pdf')",
        ),
        "file_id": ParameterSchema(
            type="string",
            required=False,
            description="Dropbox file ID (alternative to path)",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="File ID"),
        "file_name": ReturnFieldSchema(type="string", description="File name"),
        "path": ReturnFieldSchema(type="string", description="Full file path"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size"),
        "file_content": ReturnFieldSchema(type="string", description="Base64 encoded content"),
        "status": ReturnFieldSchema(type="string", description="Should be 'downloaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="File not found",
            recovery_hint="Verify path or file_id exists using dropbox.file.list",
        ),
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Dropbox OAuth credentials not configured",
            recovery_hint="User must complete Dropbox OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["dropbox.file.list", "dropbox.file.metadata"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ FILE LIST ============

DROPBOX_FILE_LIST = CapabilitySchema(
    capability_key="dropbox.file.list",
    service="dropbox",
    category="files",
    description="List files in Dropbox folder",
    description_detailed=(
        "Lists files and folders in a Dropbox folder. Use empty string or omit folder_path "
        "to list root folder contents. Supports pagination via cursor."
    ),
    parameters={
        "folder_path": ParameterSchema(
            type="string",
            required=False,
            description="Folder path (empty string for root)",
            default="",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of entries to return (max 2000)",
            default=100,
        ),
    },
    returns={
        "files": ReturnFieldSchema(
            type="array",
            description="List of file/folder objects with id, name, path, is_folder, size",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of entries returned"),
        "has_more": ReturnFieldSchema(type="boolean", description="Whether more entries exist"),
        "cursor": ReturnFieldSchema(type="string", description="Cursor for pagination"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="Folder not found",
            recovery_hint="Verify folder_path exists",
        ),
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Dropbox OAuth credentials not configured",
            recovery_hint="User must complete Dropbox OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["dropbox.file.download", "dropbox.file.metadata"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ FOLDER CREATE ============

DROPBOX_FOLDER_CREATE = CapabilitySchema(
    capability_key="dropbox.folder.create",
    service="dropbox",
    category="files",
    description="Create a folder in Dropbox",
    description_detailed=(
        "Creates a new folder in Dropbox. Can be created at root level "
        "or as a subfolder. Folders are automatically renamed if a folder "
        "with the same name exists."
    ),
    parameters={
        "folder_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the new folder",
            example="Project Documents",
        ),
        "parent_path": ParameterSchema(
            type="string",
            required=False,
            description="Parent folder path (creates at root if omitted)",
        ),
    },
    returns={
        "folder_id": ReturnFieldSchema(type="string", description="New folder ID"),
        "folder_name": ReturnFieldSchema(type="string", description="Folder name"),
        "path": ReturnFieldSchema(type="string", description="Full folder path"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Dropbox OAuth credentials not configured",
            recovery_hint="User must complete Dropbox OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["dropbox.file.upload"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ FILE METADATA ============

DROPBOX_FILE_METADATA = CapabilitySchema(
    capability_key="dropbox.file.metadata",
    service="dropbox",
    category="files",
    description="Get file metadata without downloading content",
    description_detailed=(
        "Retrieves detailed metadata for a file or folder including name, size, "
        "path, and modification time. Does not download the file content."
    ),
    parameters={
        "path": ParameterSchema(
            type="string",
            required=False,
            description="File or folder path",
        ),
        "file_id": ParameterSchema(
            type="string",
            required=False,
            description="Dropbox file ID (alternative to path)",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="File/folder ID"),
        "file_name": ReturnFieldSchema(type="string", description="File/folder name"),
        "path": ReturnFieldSchema(type="string", description="Full path"),
        "is_folder": ReturnFieldSchema(type="boolean", description="Whether item is a folder"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size (files only)"),
        "modified_time": ReturnFieldSchema(type="string", description="Last modified time"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="File or folder not found",
            recovery_hint="Verify path or file_id exists using dropbox.file.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["dropbox.file.list"],
        typically_followed_by=["dropbox.file.download"],
    ),
    idempotent=True,
    has_side_effects=False,
)

DROPBOX_SCHEMAS: dict[str, CapabilitySchema] = {
    "dropbox.file.upload": DROPBOX_FILE_UPLOAD,
    "dropbox.file.download": DROPBOX_FILE_DOWNLOAD,
    "dropbox.file.list": DROPBOX_FILE_LIST,
    "dropbox.folder.create": DROPBOX_FOLDER_CREATE,
    "dropbox.file.metadata": DROPBOX_FILE_METADATA,
}

__all__ = ["DROPBOX_SCHEMAS"]
