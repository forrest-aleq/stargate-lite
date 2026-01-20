#!/usr/bin/env python3
"""
Script to add credential_type and supports_delegation to all capabilities in registry
Run this once to update the registry for dual credential system
"""

import re
from pathlib import Path

# Define credential type mapping
CREDENTIAL_TYPE_MAP = {
    # Customer credentials - Business systems
    "quickbooks": "customer",
    "stripe": "customer",
    "billcom": "customer",
    "netsuite": "customer",
    "recurly": "customer",
    "plaid": "customer",
    "ramp": "customer",
    "mercury": "customer",
    "brex": "customer",
    "chase": "customer",
    "hubspot": "customer",
    "asana": "customer",
    "powerbi": "customer",
    "ibkr": "customer",
    "schwab": "customer",
    # Agent credentials with delegation support
    "gmail": "agent",  # Gmail can be Aleq's or delegated
    "google_calendar": "agent",  # Calendar can be Aleq's or delegated
    "outlook_calendar": "agent",  # Outlook calendar can be Aleq's or delegated
    "slack": "agent",  # Slack can be Aleq's or delegated
    # Customer credentials - Customer's files/sheets
    "google_drive": "customer",  # Customer's Drive files
    "google_sheets": "customer",  # Customer's spreadsheets
    "microsoft_excel": "customer",  # Customer's Excel files
    "microsoft_onedrive": "customer",  # Customer's OneDrive
    # Agent credentials - Aleq's internal tools
    "notion": "agent",  # Aleq's Notion workspace (no delegation)
    # No credentials
    "ocr": None,  # OCR utility doesn't need credentials
    # Communications
    "blandai": "customer",  # Customer's Bland.ai account
    "twilio": "customer",  # Customer's Twilio account
}

# Services that support delegation
SUPPORTS_DELEGATION = {"gmail", "google_calendar", "outlook_calendar", "slack"}

# Delegation instructions
DELEGATION_INSTRUCTIONS = {
    "gmail": "Create aleq@yourcompany.com email account or grant delegate access",
    "google_calendar": "Grant Aleq access to your Google Calendar",
    "outlook_calendar": "Grant Aleq access to your Outlook Calendar",
    "slack": "Add Aleq bot to your Slack workspace",
}


def determine_credential_type_from_service(service):
    """Determine credential type from service name"""
    # Direct mapping
    if service in CREDENTIAL_TYPE_MAP:
        return CREDENTIAL_TYPE_MAP[service]

    # For composite services (e.g., "google" includes gmail, drive, calendar, sheets)
    # We'll need to determine based on capability key
    if service == "google":
        return "mixed"  # Will need manual review

    if service == "microsoft":
        return "mixed"  # Will need manual review

    # Default to customer for business systems
    return "customer"


def main():
    # Resolve relative to project root (script is in tests/scripts/)
    script_dir = Path(__file__).resolve().parent
    registry_path = script_dir.parent.parent / "app" / "registry.py"

    with registry_path.open() as f:
        content = f.read()

    # Find all capability definitions
    # Pattern: "capability.key": {
    #     "handler": ...,
    #     "tool_name": ...,
    #     "description": ...,
    #     "requires_oauth": ...,
    #     "service": "..."
    # },

    # Strategy: Add credential_type and supports_delegation after "service" field

    # For each service, determine credential type and delegation support
    lines = content.split("\n")
    new_lines = []
    current_service = None

    for line in lines:
        new_lines.append(line)

        # Detect service line
        if '"service":' in line:
            # Extract service name
            match = re.search(r'"service":\s*"(\w+)"', line)
            if match:
                current_service = match.group(1)

                # Determine credential type
                cred_type = determine_credential_type_from_service(current_service)

                # Add credential_type field
                indent = len(line) - len(line.lstrip())
                spaces = " " * indent

                if cred_type == "customer":
                    new_lines.append(f'{spaces}"credential_type": "customer",')
                    new_lines.append(f'{spaces}"supports_delegation": False')
                elif cred_type == "agent":
                    new_lines.append(f'{spaces}"credential_type": "agent",')
                    if current_service in SUPPORTS_DELEGATION:
                        new_lines.append(f'{spaces}"supports_delegation": True,')
                        instr = DELEGATION_INSTRUCTIONS.get(current_service, "")
                        if instr:
                            new_lines.append(f'{spaces}"delegation_instructions": "{instr}"')
                    else:
                        new_lines.append(f'{spaces}"supports_delegation": False')
                elif cred_type is None:
                    # No credentials (OCR)
                    new_lines.append(f'{spaces}"credential_type": None,')
                    new_lines.append(f'{spaces}"supports_delegation": False')
                else:  # "mixed" - needs manual review
                    new_lines.append(f"{spaces}# TODO: Set credential_type (mixed - review)")
                    new_lines.append(
                        f'{spaces}"credential_type": "customer",  # TEMPORARY - review this'
                    )
                    new_lines.append(f'{spaces}"supports_delegation": False')

    # Write updated content
    new_content = "\n".join(new_lines)

    updated_path = registry_path.with_suffix(".py.updated")
    with updated_path.open("w") as f:
        f.write(new_content)

    print(f"✅ Updated registry written to {updated_path}")
    print("Review the file, then replace the original:")
    print(f"mv {updated_path} {registry_path}")


if __name__ == "__main__":
    main()
