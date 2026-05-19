"""
N3 Provider Contract (v1.1.0)

Declares the locked API surface that the N3 frontend can call on Stargate.
N3 only does: check connector truth/status, start/callback OAuth, check/revoke
credentials, read credential metadata. No execute. No capabilities.

Any change to this contract must be reflected in CHANGELOG.md.
"""

N3_CONTRACT: dict[str, object] = {
    "consumer": "n3",
    "version": "1.1.0",
    "description": "What the N3 frontend can call on Stargate",
    "endpoints": [
        {
            "method": "GET",
            "path": "/health",
            "auth": False,
            "response_model": "HealthResponse",
        },
        {
            "method": "POST",
            "path": "/api/v1/connectors/status",
            "auth": True,
            "request_model": "ConnectorStatusRequest",
            "response_model": "ConnectorStatusResponse",
        },
        {
            "method": "POST",
            "path": "/api/v1/connectors/connected",
            "auth": True,
            "request_model": "ConnectedServicesRequest",
            "response_model": "ConnectedServicesResponse",
        },
        {
            "method": "POST",
            "path": "/api/v1/credentials/status",
            "auth": True,
            "request_fields": ["org_id", "user_id", "capability_key"],
        },
        {
            "method": "GET",
            "path": "/api/v1/credentials/metadata",
            "auth": True,
            "query_params": ["org_id", "user_id", "service", "credential_type"],
        },
        {
            "method": "POST",
            "path": "/api/v1/credentials/revoke",
            "auth": True,
            "request_fields": ["org_id", "user_id", "service"],
        },
        {
            "method": "GET",
            "path": "/oauth/{provider}/authorize",
            "auth": False,
            "path_params": ["provider"],
            "query_params": ["org_id", "user_id"],
        },
        {
            "method": "GET",
            "path": "/oauth/{provider}/callback",
            "auth": False,
            "path_params": ["provider"],
        },
    ],
    # N3 does NOT have access to:
    "denied": [
        "POST /api/v1/execute",
        "GET /api/v1/capabilities",
        "GET /api/v1/schemas/*",
    ],
}
