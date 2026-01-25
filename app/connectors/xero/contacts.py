"""
Xero Contacts connector - Customer and Supplier management.

Reference: https://developer.xero.com/documentation/api/accounting/contacts

Contacts in Xero can be customers, suppliers, or both.
They are identified by ContactID (UUID) or ContactNumber.
"""

from typing import Any

from app.logging_config import get_logger

from .base import XeroBase

logger = get_logger(__name__)


class ContactsMixin(XeroBase):
    """Mixin providing contact management capabilities."""

    def list_contacts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List contacts with optional filtering.

        Args:
            where: Filter expression (e.g., "Name.Contains('Smith')")
            order: Sort field (e.g., "Name ASC")
            page: Page number for pagination (1-indexed)
            include_archived: Include archived contacts
            contact_type: Filter by type - "CUSTOMER", "SUPPLIER", or None for all
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        # Build where clause
        where_clauses: list[str] = []
        if args.get("where"):
            where_clauses.append(args["where"])

        contact_type = args.get("contact_type")
        if contact_type == "CUSTOMER":
            where_clauses.append("IsCustomer==true")
        elif contact_type == "SUPPLIER":
            where_clauses.append("IsSupplier==true")

        if not args.get("include_archived", False):
            where_clauses.append('ContactStatus!="ARCHIVED"')

        if where_clauses:
            params["where"] = " AND ".join(where_clauses)

        if args.get("order"):
            params["order"] = args["order"]

        page = args.get("page", 1)
        params["page"] = page

        result = self._make_api_call("GET", "Contacts", cred, tenant_id, params=params)
        contacts = result.get("Contacts", [])

        logger.info(
            "Xero contacts listed",
            service="xero",
            count=len(contacts),
            page=page,
            log_event="contacts_listed",
        )

        return {
            "contacts": [self._format_contact(c) for c in contacts],
            "count": len(contacts),
            "page": page,
            "status": "success",
        }

    def get_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific contact by ID or number.

        Args:
            contact_id: Xero ContactID (UUID)
            contact_number: Alternative - contact number
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        contact_id = args.get("contact_id") or args.get("contact_number")
        if not contact_id:
            raise ValueError("contact_id or contact_number required")

        result = self._make_api_call("GET", f"Contacts/{contact_id}", cred, tenant_id)
        contacts = result.get("Contacts", [])

        if not contacts:
            return {"contact": None, "status": "not_found"}

        contact = contacts[0]
        logger.info(
            "Xero contact retrieved",
            service="xero",
            contact_id=contact.get("ContactID"),
            log_event="contact_retrieved",
        )

        return {"contact": self._format_contact(contact), "status": "success"}

    def create_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new contact.

        Args:
            name: Contact name (required)
            email: Email address
            first_name: First name
            last_name: Last name
            phone: Phone number
            account_number: Account number for the contact
            contact_number: Your reference number
            tax_number: Tax/VAT number
            is_customer: Mark as customer
            is_supplier: Mark as supplier
            default_currency: Default currency code
            addresses: List of addresses
            bank_account_details: Bank account details
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("name"):
            raise ValueError("Contact name is required")

        contact_data: dict[str, Any] = {"Name": args["name"]}

        # Optional fields
        if args.get("email"):
            contact_data["EmailAddress"] = args["email"]
        if args.get("first_name"):
            contact_data["FirstName"] = args["first_name"]
        if args.get("last_name"):
            contact_data["LastName"] = args["last_name"]
        if args.get("contact_number"):
            contact_data["ContactNumber"] = args["contact_number"]
        if args.get("account_number"):
            contact_data["AccountNumber"] = args["account_number"]
        if args.get("tax_number"):
            contact_data["TaxNumber"] = args["tax_number"]
        if args.get("default_currency"):
            contact_data["DefaultCurrency"] = args["default_currency"]

        # Contact type flags
        if args.get("is_customer") is not None:
            contact_data["IsCustomer"] = args["is_customer"]
        if args.get("is_supplier") is not None:
            contact_data["IsSupplier"] = args["is_supplier"]

        # Phone numbers
        if args.get("phone"):
            contact_data["Phones"] = [
                {"PhoneType": "DEFAULT", "PhoneNumber": args["phone"]},
            ]

        # Addresses
        if args.get("addresses"):
            contact_data["Addresses"] = self._format_addresses_for_api(args["addresses"])

        # Bank details
        if args.get("bank_account_details"):
            contact_data["BankAccountDetails"] = args["bank_account_details"]

        result = self._make_api_call(
            "POST", "Contacts", cred, tenant_id, data={"Contacts": [contact_data]}
        )

        created = result.get("Contacts", [])[0] if result.get("Contacts") else {}
        logger.info(
            "Xero contact created",
            service="xero",
            contact_id=created.get("ContactID"),
            name=args["name"],
            log_event="contact_created",
        )

        return {"contact": self._format_contact(created), "status": "success"}

    def update_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing contact.

        Args:
            contact_id: Xero ContactID (required)
            name: Updated name
            email: Updated email
            ... (same optional fields as create_contact)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        contact_id = args.get("contact_id")
        if not contact_id:
            raise ValueError("contact_id is required")

        contact_data: dict[str, Any] = {"ContactID": contact_id}

        # Update fields if provided
        if args.get("name"):
            contact_data["Name"] = args["name"]
        if args.get("email"):
            contact_data["EmailAddress"] = args["email"]
        if args.get("first_name"):
            contact_data["FirstName"] = args["first_name"]
        if args.get("last_name"):
            contact_data["LastName"] = args["last_name"]
        if args.get("contact_number"):
            contact_data["ContactNumber"] = args["contact_number"]
        if args.get("account_number"):
            contact_data["AccountNumber"] = args["account_number"]
        if args.get("tax_number"):
            contact_data["TaxNumber"] = args["tax_number"]
        if args.get("contact_status"):
            contact_data["ContactStatus"] = args["contact_status"]

        if args.get("is_customer") is not None:
            contact_data["IsCustomer"] = args["is_customer"]
        if args.get("is_supplier") is not None:
            contact_data["IsSupplier"] = args["is_supplier"]

        if args.get("phone"):
            contact_data["Phones"] = [{"PhoneType": "DEFAULT", "PhoneNumber": args["phone"]}]

        if args.get("addresses"):
            contact_data["Addresses"] = self._format_addresses_for_api(args["addresses"])

        result = self._make_api_call(
            "POST", f"Contacts/{contact_id}", cred, tenant_id, data={"Contacts": [contact_data]}
        )

        updated = result.get("Contacts", [])[0] if result.get("Contacts") else {}
        logger.info(
            "Xero contact updated",
            service="xero",
            contact_id=contact_id,
            log_event="contact_updated",
        )

        return {"contact": self._format_contact(updated), "status": "success"}

    def archive_contact(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Archive a contact (soft delete).

        Args:
            contact_id: Xero ContactID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        contact_id = args.get("contact_id")
        if not contact_id:
            raise ValueError("contact_id is required")

        contact_data = {"ContactID": contact_id, "ContactStatus": "ARCHIVED"}

        self._make_api_call(
            "POST", f"Contacts/{contact_id}", cred, tenant_id, data={"Contacts": [contact_data]}
        )

        logger.info(
            "Xero contact archived",
            service="xero",
            contact_id=contact_id,
            log_event="contact_archived",
        )

        return {"contact_id": contact_id, "status": "archived"}

    def search_contacts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search contacts by name, email, or account number.

        Args:
            query: Search query string
            search_type: "name", "email", "account_number", or "all" (default)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        query = args.get("query", "")
        search_type = args.get("search_type", "all")

        if not query:
            raise ValueError("query is required")

        # Build where clause based on search type
        if search_type == "name":
            where = f'Name.Contains("{query}")'
        elif search_type == "email":
            where = f'EmailAddress.Contains("{query}")'
        elif search_type == "account_number":
            where = f'AccountNumber=="{query}"'
        else:  # all - search name and email
            where = f'Name.Contains("{query}") OR EmailAddress.Contains("{query}")'

        params = {"where": where}
        result = self._make_api_call("GET", "Contacts", cred, tenant_id, params=params)
        contacts = result.get("Contacts", [])

        logger.info(
            "Xero contacts searched",
            service="xero",
            query=query,
            results=len(contacts),
            log_event="contacts_searched",
        )

        return {
            "contacts": [self._format_contact(c) for c in contacts],
            "count": len(contacts),
            "query": query,
            "status": "success",
        }

    def get_contact_history(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get history/activity for a contact.

        Args:
            contact_id: Xero ContactID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        contact_id = args.get("contact_id")
        if not contact_id:
            raise ValueError("contact_id is required")

        result = self._make_api_call("GET", f"Contacts/{contact_id}/History", cred, tenant_id)
        history = result.get("HistoryRecords", [])

        return {
            "contact_id": contact_id,
            "history": [
                {
                    "date": h.get("DateUTC"),
                    "changes": h.get("Changes"),
                    "user": h.get("User"),
                    "details": h.get("Details"),
                }
                for h in history
            ],
            "count": len(history),
            "status": "success",
        }

    def _format_contact(self, contact: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero contact for API response."""
        addresses: list[dict[str, Any]] = contact.get("Addresses", [])
        phones: list[dict[str, Any]] = contact.get("Phones", [])

        # Find primary address types
        street_address: dict[str, Any] = next(
            (a for a in addresses if a.get("AddressType") == "STREET"), {}
        )
        postal_address: dict[str, Any] = next(
            (a for a in addresses if a.get("AddressType") == "POBOX"), {}
        )

        # Find phone types
        default_phone: dict[str, Any] = next(
            (p for p in phones if p.get("PhoneType") == "DEFAULT"), {}
        )
        mobile: dict[str, Any] = next((p for p in phones if p.get("PhoneType") == "MOBILE"), {})

        return {
            "contact_id": contact.get("ContactID"),
            "contact_number": contact.get("ContactNumber"),
            "account_number": contact.get("AccountNumber"),
            "name": contact.get("Name"),
            "first_name": contact.get("FirstName"),
            "last_name": contact.get("LastName"),
            "email": contact.get("EmailAddress"),
            "tax_number": contact.get("TaxNumber"),
            "status": contact.get("ContactStatus"),
            "is_customer": contact.get("IsCustomer", False),
            "is_supplier": contact.get("IsSupplier", False),
            "default_currency": contact.get("DefaultCurrency"),
            "balances": {
                "accounts_receivable": contact.get("Balances", {})
                .get("AccountsReceivable", {})
                .get("Outstanding"),
                "accounts_payable": contact.get("Balances", {})
                .get("AccountsPayable", {})
                .get("Outstanding"),
            },
            "street_address": self._format_address(street_address),
            "postal_address": self._format_address(postal_address),
            "phone": default_phone.get("PhoneNumber"),
            "mobile": mobile.get("PhoneNumber"),
            "bank_account_details": contact.get("BankAccountDetails"),
            "updated_date": contact.get("UpdatedDateUTC"),
        }

    def _format_address(self, address: dict[str, Any]) -> dict[str, Any] | None:
        """Format a Xero address for API response."""
        if not address:
            return None
        return {
            "address_type": address.get("AddressType"),
            "line1": address.get("AddressLine1"),
            "line2": address.get("AddressLine2"),
            "line3": address.get("AddressLine3"),
            "line4": address.get("AddressLine4"),
            "city": address.get("City"),
            "region": address.get("Region"),
            "postal_code": address.get("PostalCode"),
            "country": address.get("Country"),
        }

    def _format_addresses_for_api(self, addresses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format addresses for Xero API request."""
        formatted: list[dict[str, Any]] = []
        for addr in addresses:
            xero_addr: dict[str, Any] = {
                "AddressType": addr.get("address_type", "STREET"),
            }
            if addr.get("line1"):
                xero_addr["AddressLine1"] = addr["line1"]
            if addr.get("line2"):
                xero_addr["AddressLine2"] = addr["line2"]
            if addr.get("city"):
                xero_addr["City"] = addr["city"]
            if addr.get("region"):
                xero_addr["Region"] = addr["region"]
            if addr.get("postal_code"):
                xero_addr["PostalCode"] = addr["postal_code"]
            if addr.get("country"):
                xero_addr["Country"] = addr["country"]
            formatted.append(xero_addr)
        return formatted
