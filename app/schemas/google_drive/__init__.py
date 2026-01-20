"""
Google Drive Capability Schemas.

Rich metadata for file upload, download, and management via Drive API v3.
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

GDRIVE_FILE_UPLOAD = CapabilitySchema(
    capability_key="gdrive.file.upload",
    service="google",
    category="files",
    description="Upload file to Google Drive",
    description_detailed=(
        "Uploads a file to Google Drive. File content must be base64 encoded. "
        "Optionally specify a parent folder ID to upload into a specific folder."
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
        "folder_id": ParameterSchema(
            type="string",
            required=False,
            description="Parent folder ID (uploads to root if omitted)",
        ),
        "mime_type": ParameterSchema(
            type="string",
            required=False,
            description="MIME type of the file",
            default="application/octet-stream",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="Google Drive file ID"),
        "file_name": ReturnFieldSchema(type="string", description="Uploaded file name"),
        "mime_type": ReturnFieldSchema(type="string", description="File MIME type"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size in bytes"),
        "created_time": ReturnFieldSchema(type="string", description="Creation timestamp"),
        "web_view_link": ReturnFieldSchema(type="string", description="URL to view file"),
        "status": ReturnFieldSchema(type="string", description="Should be 'uploaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid file content or folder ID",
            recovery_hint="Ensure file_content is valid base64 and folder exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["gdrive.file.metadata"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ FILE DOWNLOAD ============

GDRIVE_FILE_DOWNLOAD = CapabilitySchema(
    capability_key="gdrive.file.download",
    service="google",
    category="files",
    description="Download file from Google Drive",
    description_detailed=(
        "Downloads a file from Google Drive by its file ID. "
        "Returns the file content as base64 encoded string."
    ),
    parameters={
        "file_id": ParameterSchema(
            type="string",
            required=True,
            description="Google Drive file ID",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="File ID"),
        "file_name": ReturnFieldSchema(type="string", description="File name"),
        "mime_type": ReturnFieldSchema(type="string", description="File MIME type"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size"),
        "file_content": ReturnFieldSchema(type="string", description="Base64 encoded content"),
        "status": ReturnFieldSchema(type="string", description="Should be 'downloaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="File not found",
            recovery_hint="Verify file_id exists using gdrive.file.list",
        ),
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["gdrive.file.list", "gdrive.file.metadata"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ FILE LIST ============

GDRIVE_FILE_LIST = CapabilitySchema(
    capability_key="gdrive.file.list",
    service="google",
    category="files",
    description="List files in Google Drive",
    description_detailed=(
        "Lists files in Google Drive, optionally filtered by folder or query string. "
        "Returns file metadata including IDs, names, and sizes."
    ),
    parameters={
        "folder_id": ParameterSchema(
            type="string",
            required=False,
            description="List files in specific folder (root if omitted)",
        ),
        "query": ParameterSchema(
            type="string",
            required=False,
            description="Drive query string for filtering",
            example="mimeType='application/pdf'",
        ),
        "max_results": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of files to return",
            default=100,
        ),
    },
    returns={
        "files": ReturnFieldSchema(
            type="array",
            description="List of file objects with id, name, mimeType, size, timestamps",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of files returned"),
        "next_page_token": ReturnFieldSchema(
            type="string", description="Token for pagination"
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["gdrive.file.download", "gdrive.file.metadata"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ FOLDER CREATE ============

GDRIVE_FOLDER_CREATE = CapabilitySchema(
    capability_key="gdrive.folder.create",
    service="google",
    category="files",
    description="Create a folder in Google Drive",
    description_detailed=(
        "Creates a new folder in Google Drive. Can be created at root level "
        "or as a subfolder under an existing folder."
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
            description="Parent folder ID (creates at root if omitted)",
        ),
    },
    returns={
        "folder_id": ReturnFieldSchema(type="string", description="New folder ID"),
        "folder_name": ReturnFieldSchema(type="string", description="Folder name"),
        "web_view_link": ReturnFieldSchema(type="string", description="URL to view folder"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["gdrive.file.upload"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ FILE METADATA ============

GDRIVE_FILE_METADATA = CapabilitySchema(
    capability_key="gdrive.file.metadata",
    service="google",
    category="files",
    description="Get file metadata without downloading content",
    description_detailed=(
        "Retrieves detailed metadata for a file including name, size, type, "
        "timestamps, and ownership information. Does not download the file content."
    ),
    parameters={
        "file_id": ParameterSchema(
            type="string",
            required=True,
            description="Google Drive file ID",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="File ID"),
        "file_name": ReturnFieldSchema(type="string", description="File name"),
        "mime_type": ReturnFieldSchema(type="string", description="MIME type"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size"),
        "created_time": ReturnFieldSchema(type="string", description="Creation time"),
        "modified_time": ReturnFieldSchema(type="string", description="Last modified time"),
        "web_view_link": ReturnFieldSchema(type="string", description="View URL"),
        "owners": ReturnFieldSchema(type="array", description="Owner email addresses"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="File not found",
            recovery_hint="Verify file_id exists using gdrive.file.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["gdrive.file.list"],
        typically_followed_by=["gdrive.file.download"],
    ),
    idempotent=True,
    has_side_effects=False,
)

GOOGLE_DRIVE_SCHEMAS: dict[str, CapabilitySchema] = {
    "gdrive.file.upload": GDRIVE_FILE_UPLOAD,
    "gdrive.file.download": GDRIVE_FILE_DOWNLOAD,
    "gdrive.file.list": GDRIVE_FILE_LIST,
    "gdrive.folder.create": GDRIVE_FOLDER_CREATE,
    "gdrive.file.metadata": GDRIVE_FILE_METADATA,
}

__all__ = ["GOOGLE_DRIVE_SCHEMAS"]
