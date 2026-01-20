"""
Sage Intacct Customer management connector.

Reference: https://developer.sage.com/intacct/docs/

Provides:
- Customer CRUD operations
- Customer formatting utilities
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .ap import APMixin

logger = get_logger(__name__)


class CustomerMixin(APMixin):
    """Mixin providing Customer management capabilities."""

    def list_customers(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List customers.

        Args:
            status: Filter by status - "active", "inactive"
            customer_type: Filter by type
            page_size: Results per page (default 100)
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("status"):
            filters.append(f'status eq "{args["status"]}"')
        if args.get("customer_type"):
            filters.append(f'customerType eq "{args["customer_type"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        customers = self._paginate("objects/customer", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct customers listed",
            service="sage_intacct",
            count=len(customers),
            log_event="customers_listed",
        )

        return {
            "customers": [self._format_customer(c) for c in customers],
            "count": len(customers),
            "status": "success",
        }

    def get_customer(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get a specific customer.

        Args:
            customer_id: Customer ID (required)
        """
        cred = self._get_access_token(org_id, user_id)

        customer_id = args.get("customer_id")
        if not customer_id:
            raise ValidationError("customer_id", "customer_id is required")

        result = self._make_api_call("GET", f"objects/customer/{customer_id}", cred)
        customer = result.get("ia::result", {})

        if not customer:
            return {"customer": None, "status": "not_found"}

        return {"customer": self._format_customer(customer), "status": "success"}

    def create_customer(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new customer.

        Args:
            customer_id: Customer ID (required)
            name: Customer name (required)
            print_as: Name to print on documents
            status: "active" or "inactive" (default "active")
            currency: Default currency code
            parent_id: Parent customer ID for hierarchy
            email: Primary email address
            phone: Primary phone number
            billing_address: Billing address dict
            shipping_address: Shipping address dict
            payment_terms: Payment terms (e.g., "Net 30")
            credit_limit: Credit limit amount
            tax_id: Tax ID number
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("customer_id"):
            raise ValidationError("customer_id", "customer_id is required")
        if not args.get("name"):
            raise ValidationError("name", "name is required")

        customer_data: dict[str, Any] = {
            "id": args["customer_id"],
            "name": args["name"],
        }

        if args.get("print_as"):
            customer_data["printAs"] = args["print_as"]
        if args.get("status"):
            customer_data["status"] = args["status"]
        if args.get("currency"):
            customer_data["currency"] = {"baseCurrency": args["currency"]}
        if args.get("parent_id"):
            customer_data["parent"] = {"id": args["parent_id"]}
        if args.get("email"):
            customer_data["contacts"] = {
                "primary": {"email": {"email1": args["email"]}}
            }
        if args.get("phone"):
            if "contacts" not in customer_data:
                customer_data["contacts"] = {"primary": {}}
            customer_data["contacts"]["primary"]["phone"] = {"phone1": args["phone"]}
        if args.get("payment_terms"):
            customer_data["term"] = {"name": args["payment_terms"]}
        if args.get("credit_limit"):
            customer_data["creditLimit"] = args["credit_limit"]
        if args.get("tax_id"):
            customer_data["taxId"] = args["tax_id"]

        if args.get("billing_address"):
            addr = args["billing_address"]
            customer_data["billTo"] = {
                "addressLine1": addr.get("line1"),
                "addressLine2": addr.get("line2"),
                "city": addr.get("city"),
                "stateProvince": addr.get("state"),
                "zipPostalCode": addr.get("postal_code"),
                "country": addr.get("country"),
            }

        if args.get("shipping_address"):
            addr = args["shipping_address"]
            customer_data["shipTo"] = {
                "addressLine1": addr.get("line1"),
                "addressLine2": addr.get("line2"),
                "city": addr.get("city"),
                "stateProvince": addr.get("state"),
                "zipPostalCode": addr.get("postal_code"),
                "country": addr.get("country"),
            }

        result = self._make_api_call("POST", "objects/customer", cred, data=customer_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct customer created",
            service="sage_intacct",
            customer_id=args["customer_id"],
            log_event="customer_created",
        )

        return {"customer": self._format_customer(created), "status": "success"}

    def update_customer(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing customer.

        Args:
            customer_id: Customer ID (required)
            name: Updated name
            print_as: Updated print name
            status: Updated status
            email: Updated email
            phone: Updated phone
            credit_limit: Updated credit limit
        """
        cred = self._get_access_token(org_id, user_id)

        customer_id = args.get("customer_id")
        if not customer_id:
            raise ValidationError("customer_id", "customer_id is required")

        customer_data: dict[str, Any] = {}
        if args.get("name"):
            customer_data["name"] = args["name"]
        if args.get("print_as"):
            customer_data["printAs"] = args["print_as"]
        if args.get("status"):
            customer_data["status"] = args["status"]
        if args.get("credit_limit"):
            customer_data["creditLimit"] = args["credit_limit"]

        result = self._make_api_call(
            "PATCH", f"objects/customer/{customer_id}", cred, data=customer_data
        )
        updated = result.get("ia::result", {})

        logger.info(
            "Sage Intacct customer updated",
            service="sage_intacct",
            customer_id=customer_id,
            log_event="customer_updated",
        )

        return {"customer": self._format_customer(updated), "status": "success"}

    def _format_customer(self, customer: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct customer for API response."""
        contacts = customer.get("contacts", {})
        primary = contacts.get("primary", {})

        return {
            "key": customer.get("key"),
            "customer_id": customer.get("id"),
            "name": customer.get("name"),
            "print_as": customer.get("printAs"),
            "status": customer.get("status"),
            "parent_id": customer.get("parent", {}).get("id"),
            "currency": customer.get("currency", {}).get("baseCurrency"),
            "email": primary.get("email", {}).get("email1"),
            "phone": primary.get("phone", {}).get("phone1"),
            "credit_limit": customer.get("creditLimit"),
            "tax_id": customer.get("taxId"),
            "billing_address": self._format_sage_address(customer.get("billTo", {})),
            "shipping_address": self._format_sage_address(customer.get("shipTo", {})),
            "payment_terms": customer.get("term", {}).get("name"),
            "balance_due": customer.get("totalDue"),
            "href": customer.get("href"),
        }

    def _format_sage_address(self, addr: dict[str, Any]) -> dict[str, Any] | None:
        """Format a Sage Intacct address."""
        if not addr:
            return None
        return {
            "line1": addr.get("addressLine1"),
            "line2": addr.get("addressLine2"),
            "city": addr.get("city"),
            "state": addr.get("stateProvince"),
            "postal_code": addr.get("zipPostalCode"),
            "country": addr.get("country"),
        }
