#!/usr/bin/env python3
"""
Auto-generate comprehensive capability registry documentation
For MARS team to build Subgraphs with correct capability calls
"""

import sys
from pathlib import Path

# Get project root relative to this script's location
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from collections import defaultdict

from app.registry import CAPABILITY_REGISTRY


def generate_docs():
    """Generate markdown documentation for all capabilities"""

    # Group capabilities by service
    capabilities_by_service = defaultdict(list)
    for key, config in CAPABILITY_REGISTRY.items():
        service = config["service"]
        capabilities_by_service[service].append((key, config))

    # Sort services alphabetically
    services = sorted(capabilities_by_service.keys())

    # Generate markdown
    doc = []
    doc.append("# Stargate Capability Registry")
    doc.append("")
    doc.append("**Complete API Reference for MARS Integration**")
    doc.append("")
    doc.append(f"**Total Capabilities**: {len(CAPABILITY_REGISTRY)}")
    doc.append(f"**Services**: {len(services)}")
    doc.append("")
    doc.append("**Last Updated**: October 18, 2025")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Table of contents
    doc.append("## Table of Contents")
    doc.append("")
    for service in services:
        count = len(capabilities_by_service[service])
        doc.append(f"- [{service.upper()}](#{service}) ({count} capabilities)")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Error Taxonomy section
    doc.append("## Error Taxonomy")
    doc.append("")
    doc.append("All Stargate responses include standardized error codes for MARS error handling:")
    doc.append("")
    doc.append("| Error Code | Retry Strategy | Description |")
    doc.append("|------------|---------------|-------------|")
    doc.append(
        "| `CREDENTIAL_MISSING` | `human_intervention` | User has not connected this service |"
    )
    doc.append("| `CREDENTIAL_INVALID` | `human_intervention` | Credentials expired or revoked |")
    doc.append("| `RATE_LIMIT` | `backoff` | API rate limit exceeded |")
    doc.append("| `API_DOWN` | `backoff` | External API temporarily unavailable |")
    doc.append("| `MISSING_PERMISSION` | `human_intervention` | Additional OAuth scopes required |")
    doc.append("| `VALIDATION_ERROR` | `none` | Input data from MARS was invalid |")
    doc.append("| `NOT_FOUND` | `none` | Resource does not exist |")
    doc.append(
        "| `INTERNAL_STARGATE_ERROR` | `backoff` | Internal Stargate error (bug or config issue) |"
    )
    doc.append("| `EXTERNAL_API_ERROR` | `backoff` | Generic error from external API |")
    doc.append("")
    doc.append("### Error Response Format")
    doc.append("")
    doc.append("```json")
    doc.append("{")
    doc.append('  "error": true,')
    doc.append('  "error_code": "CREDENTIAL_MISSING",')
    doc.append('  "error_message": "No credentials found for service \'quickbooks\'",')
    doc.append('  "retry_strategy": "human_intervention",')
    doc.append('  "details": {')
    doc.append('    "service": "quickbooks",')
    doc.append('    "org_id": "test_org",')
    doc.append('    "user_id": "test_user"')
    doc.append("  }")
    doc.append("}")
    doc.append("```")
    doc.append("")
    doc.append("---")
    doc.append("")

    # Generate capability listings by service
    for service in services:
        caps = sorted(capabilities_by_service[service], key=lambda x: x[0])

        doc.append(f"## {service.upper()}")
        doc.append("")
        doc.append(f"**Total Capabilities**: {len(caps)}")

        # Determine OAuth requirement
        requires_oauth = caps[0][1]["requires_oauth"] if caps else False
        auth_type = "OAuth 2.0" if requires_oauth else "API Key"
        doc.append(f"**Authentication**: {auth_type}")
        doc.append("")

        # List capabilities
        for cap_key, config in caps:
            doc.append(f"### `{cap_key}`")
            doc.append("")
            doc.append(f"**Description**: {config['description']}")
            doc.append("")
            doc.append(f"**Tool Name**: `{config['tool_name']}`")
            doc.append("")
            doc.append(f"**Requires OAuth**: `{config['requires_oauth']}`")
            doc.append("")

            # Example request
            doc.append("**Request**:")
            doc.append("```json")
            doc.append("{")
            doc.append(f'  "capability_key": "{cap_key}",')
            doc.append('  "org_id": "your_org_id",')
            doc.append('  "user_id": "your_user_id",')
            doc.append('  "args": {')

            # Add example args based on capability key patterns
            if "create" in cap_key or "upload" in cap_key:
                doc.append("    // Required fields vary by capability")
                doc.append("    // See specific implementation for details")
            elif "get" in cap_key or "retrieve" in cap_key:
                if "vendor" in cap_key:
                    doc.append('    "vendor_id": "12345"')
                elif "file" in cap_key:
                    doc.append('    "file_id": "file_id_here"')
                else:
                    doc.append('    "id": "resource_id"')
            elif "list" in cap_key:
                doc.append('    "limit": 100')
            elif "search" in cap_key or "query" in cap_key:
                doc.append('    "query": "search_term"')
            elif "update" in cap_key:
                doc.append('    "id": "resource_id",')
                doc.append("    // Updated fields here")

            doc.append("  }")
            doc.append("}")
            doc.append("```")
            doc.append("")

            # Example success response
            doc.append("**Success Response**:")
            doc.append("```json")
            doc.append("{")
            doc.append("  // Response structure varies by capability")
            doc.append("  // Typically includes resource ID and status")
            doc.append('  "status": "success"')
            doc.append("}")
            doc.append("```")
            doc.append("")

        doc.append("---")
        doc.append("")

    # Statistics
    doc.append("## Statistics")
    doc.append("")
    doc.append("### Capabilities by Service")
    doc.append("")
    doc.append("| Service | Count | Auth Type |")
    doc.append("|---------|-------|-----------|")

    for service in services:
        count = len(capabilities_by_service[service])
        auth = "OAuth" if capabilities_by_service[service][0][1]["requires_oauth"] else "API Key"
        doc.append(f"| {service} | {count} | {auth} |")

    doc.append("")
    doc.append(
        f"**Total**: {len(CAPABILITY_REGISTRY)} capabilities across {len(services)} services"
    )
    doc.append("")

    return "\n".join(doc)


if __name__ == "__main__":
    print("Generating capability registry documentation...")

    docs = generate_docs()

    output_path = PROJECT_ROOT / "CAPABILITY_REGISTRY.md"
    with output_path.open("w") as f:
        f.write(docs)

    print(f"✅ Documentation generated: {output_path}")
    print(f"   Total capabilities documented: {len(CAPABILITY_REGISTRY)}")
