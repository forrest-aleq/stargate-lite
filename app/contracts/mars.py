"""
Baby MARS Provider Contract (v1.0.0)

Declares the locked API surface for Baby MARS (Aleq): error taxonomy,
response shapes, retry strategies, capability discovery.

Any change to this contract must be reflected in CHANGELOG.md.
"""

MARS_CONTRACT: dict[str, object] = {
    "consumer": "baby_mars",
    "version": "1.0.0",
    "description": "What Baby MARS (Aleq) can call on Stargate",
    # -- Endpoints ----------------------------------------------------------
    "endpoints": [
        {
            "method": "POST",
            "path": "/api/v1/execute",
            "auth": True,
            "request_model": "ToolExecutionRequest",
            "success_model": "ToolExecutionResponse",
            "error_model": "ErrorResponse",
            "idempotent": True,
            "idempotency_ttl_seconds": 86400,
            "rate_limited": True,
            "rate_limit_default": "100/min per org_id",
        },
        {
            "method": "GET",
            "path": "/api/v1/capabilities",
            "auth": True,
        },
        {
            "method": "GET",
            "path": "/api/v1/schemas/{capability_key}",
            "auth": True,
        },
        {
            "method": "GET",
            "path": "/health",
            "auth": False,
            "response_model": "HealthResponse",
        },
    ],
    # -- Execute Request (locked fields) ------------------------------------
    "execute_request": {
        "required": ["capability_key", "org_id", "user_id", "turn_id"],
        "optional": ["args", "use_delegation", "session_id"],
        "headers": {
            "X-API-Key": "required",
            "X-Session-ID": "optional — overrides body session_id",
        },
    },
    # -- Success Response (locked shape) ------------------------------------
    "success_response": {
        "required": [
            "status",
            "capability_key",
            "tool_used",
            "outputs",
            "logs",
            "timestamp",
        ],
        "optional": ["credential_type", "error"],
        "status_value": "success",
        "http_code": 200,
    },
    # -- Error Response (locked shape) --------------------------------------
    "error_response": {
        "required": [
            "status",
            "error_code",
            "error_message",
            "retry_strategy",
            "timestamp",
        ],
        "optional": ["details", "capability_key"],
        "status_value": "error",
        "http_code": 200,
    },
    # -- Error Taxonomy (locked — 10 codes, 3 strategies) -------------------
    "error_codes": {
        "CAPABILITY_NOT_FOUND": {
            "retry": "none",
            "meaning": "Unknown capability_key",
        },
        "CREDENTIALS_MISSING": {
            "retry": "human_intervention",
            "meaning": "User hasn't connected this service",
        },
        "CREDENTIALS_INVALID": {
            "retry": "human_intervention",
            "meaning": "Token expired or revoked, re-auth needed",
        },
        "CREDENTIALS_INSUFFICIENT": {
            "retry": "human_intervention",
            "meaning": "Missing OAuth scopes",
        },
        "RATE_LIMIT": {
            "retry": "backoff",
            "meaning": "Too many requests — check retry_after in details",
        },
        "NETWORK_ERROR": {
            "retry": "backoff",
            "meaning": "Upstream API unreachable",
        },
        "VALIDATION_ERROR": {
            "retry": "none",
            "meaning": "Bad args — fix input and retry",
        },
        "EXECUTION_ERROR": {
            "retry": "backoff",
            "meaning": "Tool failed — may be transient",
        },
        "QUOTA_EXCEEDED": {
            "retry": "human_intervention",
            "meaning": "External service quota hit",
        },
        "PERMISSION_DENIED": {
            "retry": "human_intervention",
            "meaning": "User lacks required permission/scope",
        },
    },
    "retry_strategies": ["none", "backoff", "human_intervention"],
    # -- Batch behavior -----------------------------------------------------
    "batch_rules": {
        "halt_on_retry_none": True,
        "halt_on_human_intervention": True,
        "continue_on_backoff": False,
    },
    # -- Credential types ---------------------------------------------------
    "credential_types": {
        "customer": "Per-user OAuth token (user's own QuickBooks, Gmail, etc.)",
        "agent": "System credential (Aleq's own API keys, user_id='ALEQ_AGENT')",
    },
    # -- Guarantees ---------------------------------------------------------
    "guarantees": {
        "http_200_always": (
            "Errors return HTTP 200 with status='error' "
            "— never 4xx/5xx for business errors"
        ),
        "idempotency": (
            "Same turn_id + capability_key within 24h returns cached response"
        ),
        "multi_tenant_isolation": (
            "Credentials keyed by org_id:user_id:service — never cross-org"
        ),
        "token_refresh": (
            "Expired OAuth tokens auto-refreshed transparently "
            "— CREDENTIALS_INVALID only on refresh failure"
        ),
    },
}
