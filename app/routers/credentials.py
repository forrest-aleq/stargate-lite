"""
Credentials and capabilities routes for Stargate Lite.
"""

from typing import Any

from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.database import CredentialManager
from app.registry import get_capability, list_capabilities

router = APIRouter(prefix="/api/v1", tags=["credentials"])


@router.get("/capabilities")
async def get_capabilities(_: bool = Depends(verify_api_key)) -> dict[str, Any]:
    """List all available capabilities"""
    return {
        "capabilities": list_capabilities(),
        "count": len(list_capabilities()),
    }


@router.post("/credentials/status")
async def check_credential_status(
    request: dict[str, Any], _: bool = Depends(verify_api_key)
) -> dict[str, Any]:
    """
    Check if credentials exist for a capability before execution

    Request body:
    {
        "org_id": "org_123",
        "user_id": "user_456",
        "capability_key": "vendor.create",
        "use_delegation": false
    }

    Returns:
    - credential_available: bool
    - credential_type: "agent" | "customer" | None
    - access_pattern: "programmatic" | "delegate" | None (for agent credentials)
    - requires_setup: bool (True if credential missing)
    - delegation_supported: bool (True if this capability supports delegation)
    - delegation_instructions: str (setup instructions if delegation supported)
    """
    try:
        org_id = request.get("org_id")
        user_id = request.get("user_id")
        capability_key = request.get("capability_key")
        use_delegation = request.get("use_delegation", False)

        capability = get_capability(str(capability_key))
        if not capability:
            return {
                "credential_available": False,
                "credential_type": None,
                "requires_setup": False,
                "error": f"Capability '{capability_key}' not found",
            }

        # Check if OAuth is required
        if not capability.get("requires_oauth"):
            return {
                "credential_available": True,
                "credential_type": None,
                "requires_setup": False,
                "message": "No credentials required for this capability",
            }

        # Get credential using the dual credential system
        cred = CredentialManager.get_credential_for_capability(
            capability_key=str(capability_key),
            org_id=str(org_id),
            user_id=str(user_id),
            use_delegation=bool(use_delegation),
        )

        if cred:
            token_expiry = cred.get("token_expiry")
            return {
                "credential_available": True,
                "credential_type": cred.get("credential_type"),
                "access_pattern": cred.get("access_pattern"),
                "token_expiry": (token_expiry.isoformat() if token_expiry is not None else None),
                "requires_setup": False,
                "delegation_supported": capability.get("supports_delegation", False),
                "delegation_instructions": capability.get("delegation_instructions"),
            }
        else:
            # No credential found
            cred_type = capability.get("credential_type")
            return {
                "credential_available": False,
                "credential_type": cred_type,
                "requires_setup": True,
                "delegation_supported": capability.get("supports_delegation", False),
                "delegation_instructions": capability.get("delegation_instructions"),
                "message": f"Missing {cred_type} credential for {capability['service']}",
            }

    except Exception as e:
        return {
            "credential_available": False,
            "credential_type": None,
            "requires_setup": True,
            "error": str(e),
        }


@router.get("/credentials/metadata")
async def get_credential_metadata(
    org_id: str,
    user_id: str,
    service: str,
    credential_type: str = "customer",
    _: bool = Depends(verify_api_key),
) -> dict[str, Any]:
    """
    Get metadata about a stored credential (without exposing tokens)

    Query params:
    - org_id: Organization ID
    - user_id: User ID
    - service: Service name (e.g., "quickbooks", "google")
    - credential_type: "agent" or "customer" (default: "customer")

    Returns credential metadata: expiry, realm_id, etc. without exposing access_token
    """
    try:
        cred = CredentialManager.get_credential(
            org_id=org_id, user_id=user_id, service=service, credential_type=credential_type
        )

        if not cred:
            return {
                "exists": False,
                "message": f"No {credential_type} credential found for {service}",
            }

        # Return metadata without tokens
        token_expiry = cred.get("token_expiry")
        return {
            "exists": True,
            "service": service,
            "credential_type": cred.get("credential_type"),
            "access_pattern": cred.get("access_pattern"),
            "token_expiry": (token_expiry.isoformat() if token_expiry is not None else None),
            "realm_id": cred.get("realm_id"),
            "extra_data": cred.get("extra_data", {}),
        }

    except Exception as e:
        return {"exists": False, "error": str(e)}
