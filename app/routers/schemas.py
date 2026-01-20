"""
Schema API routes for Stargate Lite.

Provides endpoints for AI agents to discover rich capability metadata.
"""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.registry import CAPABILITY_REGISTRY
from app.schemas import get_schema, get_services_with_schemas, has_schema, list_schemas

router = APIRouter(prefix="/api/v1", tags=["schemas"])


def _get_api_key_verifier() -> Callable[..., bool]:
    """Import verify_api_key lazily to avoid circular imports."""
    from app.main import verify_api_key

    return verify_api_key


@router.get("/schemas")
async def list_capability_schemas(
    service: str | None = Query(None, description="Filter schemas by service name"),
    _: bool = Depends(_get_api_key_verifier()),
) -> dict[str, Any]:
    """
    List all available capability schemas.

    Returns rich metadata for capabilities that have schemas defined.
    Use the optional 'service' query parameter to filter by service.

    Response format:
    {
        "schemas": {
            "vendor.create": { ... full schema ... },
            "vendor.get": { ... },
            ...
        },
        "count": 10,
        "service_filter": "quickbooks" | null
    }
    """
    schemas = list_schemas(service=service)

    return {
        "schemas": {key: schema.model_dump() for key, schema in schemas.items()},
        "count": len(schemas),
        "service_filter": service,
    }


@router.get("/schemas/{capability_key:path}")
async def get_capability_schema(
    capability_key: str,
    _: bool = Depends(_get_api_key_verifier()),
) -> dict[str, Any]:
    """
    Get detailed schema for a specific capability.

    Returns rich metadata including parameters, returns, errors, and workflow hints.
    The capability_key should match the key used in /api/v1/execute.

    Combines schema metadata with registry metadata for complete information.
    """
    schema = get_schema(capability_key)

    if not schema:
        # Check if capability exists but has no schema
        if capability_key in CAPABILITY_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "schema_not_found",
                    "message": (
                        f"Capability '{capability_key}' exists but has no schema defined yet"
                    ),
                    "capability_exists": True,
                },
            )
        raise HTTPException(
            status_code=404,
            detail={
                "error": "capability_not_found",
                "message": f"Capability '{capability_key}' not found",
                "capability_exists": False,
            },
        )

    # Get registry metadata to combine with schema
    registry_entry = CAPABILITY_REGISTRY.get(capability_key, {})

    response = schema.model_dump()
    response.update(
        {
            "tool_name": registry_entry.get("tool_name"),
            "requires_oauth": registry_entry.get("requires_oauth", True),
            "credential_type": registry_entry.get("credential_type", "customer"),
            "supports_delegation": registry_entry.get("supports_delegation", False),
        }
    )

    return response


@router.get("/services")
async def list_services_with_schemas(
    _: bool = Depends(_get_api_key_verifier()),
) -> dict[str, Any]:
    """
    Get summary of services that have capability schemas defined.

    Useful for progressive disclosure - AI agents can first discover which
    services have rich metadata, then drill down into specific capabilities.

    Response format:
    {
        "services": {
            "quickbooks": {
                "capabilities_count": 10,
                "categories": ["vendors", "bills"]
            }
        },
        "total_services": 1,
        "total_capabilities": 10
    }
    """
    services = get_services_with_schemas()

    total_capabilities = sum(s["capabilities_count"] for s in services.values())

    return {
        "services": services,
        "total_services": len(services),
        "total_capabilities": total_capabilities,
    }


@router.get("/capabilities/enhanced")
async def list_capabilities_enhanced(
    service: str | None = Query(None, description="Filter by service name"),
    schema_only: bool = Query(False, description="Only return capabilities with schemas"),
    _: bool = Depends(_get_api_key_verifier()),
) -> dict[str, Any]:
    """
    List capabilities with schema availability indicator.

    Returns all capabilities with a 'schema_available' field indicating
    whether rich metadata is available for each capability.

    This is useful for AI agents to know which capabilities have detailed
    documentation vs. basic registry entries.
    """
    capabilities = {}

    for key, config in CAPABILITY_REGISTRY.items():
        # Apply service filter if provided
        if service and config.get("service") != service:
            continue

        has_schema_flag = has_schema(key)

        # Skip if schema_only is True and no schema exists
        if schema_only and not has_schema_flag:
            continue

        capabilities[key] = {
            "tool_name": config["tool_name"],
            "description": config["description"],
            "service": config["service"],
            "credential_type": config.get("credential_type", "customer"),
            "supports_delegation": config.get("supports_delegation", False),
            "requires_oauth": config["requires_oauth"],
            "schema_available": has_schema_flag,
        }

    return {
        "capabilities": capabilities,
        "count": len(capabilities),
        "service_filter": service,
        "schema_only": schema_only,
    }
