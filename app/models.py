"""
Pydantic models for Stargate Lite API

These models define the API contract between Stargate and its consumers.
All public models are automatically included in the OpenAPI specification.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now, suitable for Pydantic default_factory."""
    return datetime.now(UTC)


# ============================================================================
# Enums (Contract v1.0)
# ============================================================================


class ErrorCode(StrEnum):
    """Standardized error codes for Stargate API (Contract v1.0)

    These codes allow consumers to programmatically handle errors
    and determine appropriate retry strategies.
    """

    CAPABILITY_NOT_FOUND = "CAPABILITY_NOT_FOUND"
    CREDENTIALS_MISSING = "CREDENTIALS_MISSING"
    CREDENTIALS_INVALID = "CREDENTIALS_INVALID"
    CREDENTIALS_INSUFFICIENT = "CREDENTIALS_INSUFFICIENT"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK_ERROR = "NETWORK_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class RetryStrategy(StrEnum):
    """Recommended retry strategy for each error type

    Consumers should follow these strategies when handling errors.
    """

    HUMAN_INTERVENTION = "human_intervention"  # User must fix (reconnect, grant permission)
    BACKOFF = "backoff"  # Retry with exponential backoff
    NONE = "none"  # Do not retry


# ============================================================================
# Request/Response Models
# ============================================================================


class CapabilityInfo(BaseModel):
    """Schema for a single capability entry."""

    tool_name: str = Field(..., description="Underlying tool (e.g., 'quickbooks.create_vendor')")
    description: str = Field(..., description="Human-readable description")
    service: str = Field(..., description="Service name (e.g., 'quickbooks', 'stripe')")
    credential_type: str | None = Field(None, description="'customer', 'agent', or null")
    supports_delegation: bool = Field(..., description="Whether delegation is supported")
    requires_oauth: bool = Field(..., description="Whether OAuth credentials are needed")
    schema_available: bool = Field(..., description="Whether input schema is available")


class CapabilitiesResponse(BaseModel):
    """Response model for GET /api/v1/capabilities."""

    capabilities: dict[str, CapabilityInfo] = Field(
        ..., description="Map of capability_key to capability info"
    )
    count: int = Field(..., description="Total number of capabilities")


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
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Execution metadata from caller (verb_tier, proactive, etc.)",
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
                "metadata": None,
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
    timestamp: datetime = Field(default_factory=_utcnow, description="Execution timestamp")

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
    """Model for storing OAuth credentials (internal use only - not exposed in OpenAPI)"""

    org_id: str = Field(..., description="Organization ID for multi-tenancy")
    user_id: str = Field(..., description="User ID for credential lookup")
    service: str = Field(
        ..., description="Service name (e.g., 'quickbooks', 'hubspot', 'google', 'slack')"
    )
    access_token: str = Field(..., description="OAuth access token (encrypted at rest)")
    refresh_token: str | None = Field(None, description="OAuth refresh token for token renewal")
    token_expiry: datetime | None = Field(None, description="When the access token expires")
    realm_id: str | None = Field(None, description="QuickBooks-specific realm/company ID")
    extra_data: dict[str, Any] = Field(
        default_factory=dict, description="Additional service-specific data"
    )


class HealthResponse(BaseModel):
    """Health check response for /health endpoint"""

    status: str = Field(..., description="Service status: 'healthy' or 'degraded'")
    version: str = Field(..., description="Stargate Lite version (e.g., '0.9.0')")
    capabilities_count: int | None = Field(None, description="Total registered capabilities")
    timestamp: datetime = Field(default_factory=_utcnow, description="Response timestamp (UTC)")
    services: dict[str, str] = Field(
        default_factory=dict, description="Status of dependent services"
    )

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "status": "healthy",
                "version": "0.9.0",
                "capabilities_count": 570,
                "timestamp": "2025-10-18T12:00:00.123456",
                "services": {"database": "connected", "redis": "connected"},
            }
        }


class ConnectorStatus(BaseModel):
    """Status for a single connector (admin endpoint)"""

    service: str = Field(..., description="Service name (e.g., 'quickbooks', 'stripe')")
    credential_status: str = Field(
        ..., description="Credential status: 'connected', 'expired', or 'missing'"
    )
    token_expiry: datetime | None = Field(None, description="When the token expires (if OAuth)")
    last_updated: datetime | None = Field(None, description="When credential was last refreshed")
    requires_oauth: bool = Field(..., description="Whether this service requires OAuth flow")
    connection_count: int = Field(
        default=0, description="Number of org:user combinations with this credential"
    )

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "service": "quickbooks",
                "credential_status": "connected",
                "token_expiry": "2025-12-31T23:59:59",
                "last_updated": "2025-10-18T10:00:00",
                "requires_oauth": True,
                "connection_count": 5,
            }
        }


class ConnectorHealthResponse(BaseModel):
    """Detailed health check for all connectors (admin endpoint)"""

    status: str = Field(..., description="Overall status: 'healthy' or 'degraded'")
    version: str = Field(..., description="Stargate Lite version")
    total_connectors: int = Field(..., description="Total number of connector types")
    total_connections: int = Field(..., description="Total credential records across all services")
    connectors: list[ConnectorStatus] = Field(
        ..., description="Status of each individual connector"
    )
    timestamp: datetime = Field(default_factory=_utcnow, description="Response timestamp (UTC)")

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "status": "healthy",
                "version": "0.9.0",
                "total_connectors": 13,
                "total_connections": 25,
                "connectors": [
                    {
                        "service": "quickbooks",
                        "credential_status": "connected",
                        "requires_oauth": True,
                        "connection_count": 5,
                    }
                ],
                "timestamp": "2025-10-18T12:00:00.123456",
            }
        }


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

    connectors: list[WorkflowConnectorStatus] = Field(
        ..., description="Status of each requested connector"
    )
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


# ============================================================================
# Error Response Models (Contract v1.0)
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response format (Contract v1.0)

    Business errors return HTTP 200 with status='error'. Rate-limit
    errors return HTTP 429. The error_code field allows programmatic
    error classification and retry strategy selection.
    """

    status: str = Field(default="error", description="Always 'error' for error responses")
    error_code: ErrorCode = Field(
        ..., description="Machine-readable error code for programmatic handling"
    )
    error_message: str = Field(..., description="Human-readable error description")
    retry_strategy: RetryStrategy = Field(
        ..., description="Recommended retry strategy for this error type"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error context (e.g., field, service)"
    )
    capability_key: str | None = Field(
        None, description="The capability that was being executed (if applicable)"
    )
    timestamp: datetime = Field(
        default_factory=_utcnow, description="When the error occurred (UTC)"
    )

    class Config:
        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "status": "error",
                "error_code": "CREDENTIALS_MISSING",
                "error_message": "No credentials found for service 'quickbooks'",
                "retry_strategy": "human_intervention",
                "details": {"service": "quickbooks", "org_id": "org_123"},
                "capability_key": "vendor.create",
                "timestamp": "2025-10-18T12:00:00.123456",
            }
        }
