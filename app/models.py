"""
Pydantic models for Stargate Lite API
"""

from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution (Contract v1.0 compliant)"""

    capability_key: str = Field(
        ..., description="The capability being requested (e.g., 'vendor.create')"
    )
    org_id: str = Field(..., description="Organization ID for multi-tenancy")
    user_id: str = Field(..., description="User ID for credential lookup and audit")
    turn_id: str = Field(
        ..., description="Turn ID for idempotency (prevents duplicate executions) - REQUIRED"
    )
    args: dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the tool execution"
    )
    use_delegation: bool = Field(
        default=False,
        description="For agent credentials: prefer delegated access over system credentials",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID for event correlation (passed via X-Session-ID header or body)",
    )

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "capability_key": "vendor.create",
                "org_id": "org_12345",
                "user_id": "user_67890",
                "turn_id": "turn_01HZ8Y3K5G4N2M6X9W7Q",
                "args": {"vendor_name": "Acme Inc.", "email": "[email protected]"},
                "use_delegation": False,
                "session_id": "01936b3a-4f2e-7000-8000-abc123def456",
            }
        }


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution"""

    status: str = Field(..., description="Execution status: 'success' or 'error'")
    capability_key: str = Field(..., description="The capability that was executed")
    tool_used: str = Field(
        ..., description="The actual tool/connector used (e.g., 'quickbooks.create_vendor')"
    )
    outputs: dict[str, Any] = Field(default_factory=dict, description="Outputs from the execution")
    logs: list[str] = Field(default_factory=list, description="Execution logs")
    error: str | None = Field(None, description="Error message if status is 'error'")
    credential_type: str | None = Field(
        None, description="Type of credential used: 'agent' or 'customer' or None"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "status": "success",
                "capability_key": "vendor.create",
                "tool_used": "quickbooks.create_vendor",
                "outputs": {
                    "vendor_id": "qb:123-xyz",
                    "status": "pending_w9",
                    "created_at": "2025-10-18T12:00:00Z",
                },
                "logs": ["Successfully created vendor in QuickBooks"],
                "credential_type": "customer",
                "timestamp": "2025-10-18T12:00:00.123456",
            }
        }


class OAuthCredential(BaseModel):
    """Model for storing OAuth credentials"""

    org_id: str
    user_id: str
    service: str  # quickbooks, hubspot, google, slack
    access_token: str
    refresh_token: str | None = None
    token_expiry: datetime | None = None
    realm_id: str | None = None  # QuickBooks specific
    extra_data: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    capabilities_count: int | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, str] = Field(default_factory=dict)


class ConnectorStatus(BaseModel):
    """Status for a single connector"""

    service: str
    credential_status: str  # "connected", "expired", "missing"
    token_expiry: datetime | None = None
    last_updated: datetime | None = None
    requires_oauth: bool
    connection_count: int = 0  # Number of org:user combos with this credential


class ConnectorHealthResponse(BaseModel):
    """Detailed health check for all connectors"""

    status: str
    version: str
    total_connectors: int
    total_connections: int  # Total credential records
    connectors: list[ConnectorStatus]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConnectorStatusRequest(BaseModel):
    """Request to check connector status for specific services"""

    org_id: str = Field(..., description="Organization ID")
    user_id: str = Field(..., description="User ID")
    services: list[str] = Field(
        ..., description="List of services to check (e.g., ['quickbooks', 'gmail'])"
    )

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "org_id": "org_12345",
                "user_id": "user_67890",
                "services": ["quickbooks", "gmail", "vision"],
            }
        }


class WorkflowConnectorStatus(BaseModel):
    """Status for a single connector in workflow context"""

    kind: str = Field(..., description="Service name (e.g., 'quickbooks', 'gmail')")
    display_name: str = Field(..., description="Human-readable name (e.g., 'QuickBooks')")
    status: str = Field(..., description="Auth status: 'connected', 'expired', 'missing'")
    requires_oauth: bool = Field(..., description="Whether this service requires OAuth")
    credential_type: str | None = Field(None, description="'agent' or 'customer' or None")
    token_expiry: datetime | None = Field(None, description="When token expires (if applicable)")
    last_updated: datetime | None = Field(None, description="When credential was last updated")

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "kind": "quickbooks",
                "display_name": "QuickBooks",
                "status": "connected",
                "requires_oauth": True,
                "credential_type": "customer",
                "token_expiry": "2025-12-31T23:59:59",
                "last_updated": "2025-10-30T10:00:00",
            }
        }


class ConnectorStatusResponse(BaseModel):
    """Response with connector status for specific services"""

    connectors: list[WorkflowConnectorStatus]
    all_connected: bool = Field(
        ..., description="True if all required connectors are authenticated"
    )
    missing_count: int = Field(..., description="Number of connectors that need authentication")

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "connectors": [
                    {
                        "kind": "quickbooks",
                        "display_name": "QuickBooks",
                        "status": "connected",
                        "requires_oauth": True,
                        "credential_type": "customer",
                        "token_expiry": "2025-12-31T23:59:59",
                        "last_updated": "2025-10-30T10:00:00",
                    },
                    {
                        "kind": "gmail",
                        "display_name": "Gmail",
                        "status": "missing",
                        "requires_oauth": True,
                        "credential_type": "agent",
                        "token_expiry": None,
                        "last_updated": None,
                    },
                ],
                "all_connected": False,
                "missing_count": 1,
            }
        }
