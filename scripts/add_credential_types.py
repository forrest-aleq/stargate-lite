#!/usr/bin/env python3
"""
Add credential_type and supports_delegation to all capabilities in registry
Based on management decisions for dual credential system
"""

# Credential type rules based on management decisions
CREDENTIAL_RULES = {
    # Customer credentials ONLY - Business systems
    "quickbooks": {"type": "customer", "delegation": False},
    "stripe": {"type": "customer", "delegation": False},
    "billcom": {"type": "customer", "delegation": False},
    "netsuite": {"type": "customer", "delegation": False},
    "recurly": {"type": "customer", "delegation": False},
    "plaid": {"type": "customer", "delegation": False},
    "ramp": {"type": "customer", "delegation": False},
    "mercury": {"type": "customer", "delegation": False},
    "brex": {"type": "customer", "delegation": False},
    "chase": {"type": "customer", "delegation": False},
    "hubspot": {"type": "customer", "delegation": False},
    "asana": {"type": "customer", "delegation": False},
    "powerbi": {"type": "customer", "delegation": False},
    "ibkr": {"type": "customer", "delegation": False},
    "schwab": {"type": "customer", "delegation": False},
    "blandai": {"type": "customer", "delegation": False},
    "twilio": {"type": "customer", "delegation": False},
    # Agent credentials - Aleq's internal tools (no delegation)
    "notion": {"type": "agent", "delegation": False},
    # No credentials
    "ocr": {"type": None, "delegation": False},
    # Mixed - Google and Microsoft need capability-level decisions
    "google": "MANUAL",  # Gmail=agent+delegation, Drive/Sheets=customer
    "microsoft": "MANUAL",  # Outlook=agent+delegation, Excel/OneDrive=customer
    "slack": {
        "type": "agent",
        "delegation": True,
        "instructions": "Add Aleq bot to your Slack workspace",
    },
}

# Manual categorization for google/microsoft capabilities
GOOGLE_CAPABILITIES = {
    # Agent with delegation (email, calendar)
    "email.send": {
        "type": "agent",
        "delegation": True,
        "instructions": "Create aleq@yourcompany.com email account or grant delegate access",
    },
    "email.read": {
        "type": "agent",
        "delegation": True,
        "instructions": "Create aleq@yourcompany.com email account or grant delegate access",
    },
    "email.draft": {
        "type": "agent",
        "delegation": True,
        "instructions": "Create aleq@yourcompany.com email account or grant delegate access",
    },
    "gcal.event.create": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Google Calendar",
    },
    "gcal.availability.check": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Google Calendar",
    },
    "gcal.event.update": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Google Calendar",
    },
    "gcal.event.list": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Google Calendar",
    },
    "gcal.event.cancel": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Google Calendar",
    },
    # Customer (drive, sheets - customer's files)
    "gdrive.file.upload": {"type": "customer", "delegation": False},
    "gdrive.file.download": {"type": "customer", "delegation": False},
    "gdrive.file.list": {"type": "customer", "delegation": False},
    "gdrive.folder.create": {"type": "customer", "delegation": False},
    "gdrive.file.metadata": {"type": "customer", "delegation": False},
    "gsheets.range.get": {"type": "customer", "delegation": False},
    "gsheets.range.update": {"type": "customer", "delegation": False},
    "gsheets.row.append": {"type": "customer", "delegation": False},
    "gsheets.sheet.create": {"type": "customer", "delegation": False},
    "gsheets.batch.update": {"type": "customer", "delegation": False},
    "gsheets.range.clear": {"type": "customer", "delegation": False},
    "gsheets.metadata.get": {"type": "customer", "delegation": False},
}

MICROSOFT_CAPABILITIES = {
    # Agent with delegation (outlook calendar)
    "outlook.event.create": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Outlook Calendar",
    },
    "outlook.availability.check": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Outlook Calendar",
    },
    "outlook.event.update": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Outlook Calendar",
    },
    "outlook.event.list": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Outlook Calendar",
    },
    "outlook.event.cancel": {
        "type": "agent",
        "delegation": True,
        "instructions": "Grant Aleq access to your Outlook Calendar",
    },
    # Customer (excel, onedrive - customer's files)
    "excel.range.get": {"type": "customer", "delegation": False},
    "excel.range.update": {"type": "customer", "delegation": False},
    "excel.row.append": {"type": "customer", "delegation": False},
    "excel.worksheet.create": {"type": "customer", "delegation": False},
    "excel.worksheet.list": {"type": "customer", "delegation": False},
    "excel.table.create": {"type": "customer", "delegation": False},
    "onedrive.file.upload": {"type": "customer", "delegation": False},
    "onedrive.file.download": {"type": "customer", "delegation": False},
    "onedrive.file.list": {"type": "customer", "delegation": False},
    "onedrive.folder.create": {"type": "customer", "delegation": False},
    "onedrive.file.metadata": {"type": "customer", "delegation": False},
}


def get_credential_info(capability_key, service):
    """Get credential type info for a capability"""
    # Check manual mappings first
    if capability_key in GOOGLE_CAPABILITIES:
        return GOOGLE_CAPABILITIES[capability_key]
    if capability_key in MICROSOFT_CAPABILITIES:
        return MICROSOFT_CAPABILITIES[capability_key]

    # Check service-level rules
    if service in CREDENTIAL_RULES:
        rule = CREDENTIAL_RULES[service]
        if rule == "MANUAL":
            print(f"WARNING: {capability_key} has service '{service}' which needs manual review")
            return {"type": "customer", "delegation": False}  # Default
        return rule

    # Default to customer
    print(f"WARNING: Unknown service '{service}' for {capability_key}, defaulting to customer")
    return {"type": "customer", "delegation": False}


def main():
    registry_path = "app/registry.py"

    with open(registry_path) as f:
        lines = f.readlines()

    new_lines = []
    current_capability = None
    current_service = None

    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Detect capability key (starts with quote, ends with ": {")
        if '": {' in line and not line.strip().startswith("#"):
            # Extract capability key
            match = line.strip().split('"')[1] if '"' in line else None
            if match:
                current_capability = match

        # Detect service line
        if '"service":' in line and current_capability:
            # Extract service name
            service_match = line.split('"service":')[1].strip().strip('",')
            if service_match:
                current_service = service_match.strip('"')

                # Get credential info
                cred_info = get_credential_info(current_capability, current_service)

                # Add comma to service line if missing
                if not line.rstrip().endswith(","):
                    # Remove the last appended line and add it back with comma
                    new_lines[-1] = line.rstrip() + ",\n"

                # Add credential_type and supports_delegation
                indent = len(line) - len(line.lstrip())
                spaces = " " * indent

                # Add credential_type
                if cred_info["type"] is None:
                    new_lines.append(f'{spaces}"credential_type": None,\n')
                else:
                    new_lines.append(f'{spaces}"credential_type": "{cred_info["type"]}",\n')

                # Add supports_delegation
                delegation_val = "True" if cred_info["delegation"] else "False"
                if cred_info.get("instructions"):
                    new_lines.append(f'{spaces}"supports_delegation": {delegation_val},\n')
                    new_lines.append(
                        f'{spaces}"delegation_instructions": "{cred_info["instructions"]}"\n'
                    )
                else:
                    new_lines.append(f'{spaces}"supports_delegation": {delegation_val}\n')

        i += 1

    # Write updated registry
    with open(registry_path, "w") as f:
        f.writelines(new_lines)

    print("✅ Registry updated with credential_type and supports_delegation")
    print(f"Updated {registry_path}")


if __name__ == "__main__":
    main()
