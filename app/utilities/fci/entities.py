"""
FCI Entity Lookup Mixin.

Provides cross-service entity resolution:
- Customer lookup (QB, Stripe, Shopify, HubSpot, Recurly, Square)
- Vendor lookup (QB, Xero, Bill.com, NetSuite, Sage Intacct)
- Invoice lookup (QB, Xero, Stripe, Recurly, Square)

Supports exact and fuzzy matching with confidence scores.
"""

import re
from typing import Any

from app.logging_config import get_logger


def _sanitize_qboql(value: str) -> str:
    """
    Sanitize a value for use in QuickBooks Query Language (QBOQL).

    QBOQL uses backslash escaping for special characters.
    This prevents injection attacks in LIKE/WHERE clauses.
    """
    if not value:
        return ""
    # Escape backslashes first, then single quotes
    sanitized = value.replace("\\", "\\\\").replace("'", "\\'")
    # Remove any other potentially dangerous characters
    sanitized = re.sub(r"[;\-\-]", "", sanitized)
    return sanitized


from app.utilities.fci.service_mappings import (
    CUSTOMER_SERVICES,
    INVOICE_SERVICES,
    VENDOR_SERVICES,
)

logger = get_logger(__name__)


class EntityMixin:
    """Mixin for cross-service entity lookup."""

    def lookup_customer(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Look up a customer across all connected services.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - name: Customer name to search (partial/fuzzy)
                - email: Customer email (exact match preferred)
                - id: Customer ID with service prefix (e.g., 'qb:123', 'stripe:cus_xxx')
                - services: Limit search to specific services (list)
                - fuzzy: Enable fuzzy name matching (default: False)

        Returns:
            {
                "matches": [{service, id, name, email, confidence}],
                "primary": {service, id, name, email, balance, last_activity},
                "match_count": int,
                "lastUpdated": str,
                "sources": [str],
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        name = args.get("name")
        email = args.get("email")
        customer_id = args.get("id")
        services_filter = args.get("services", [])
        fuzzy = args.get("fuzzy", False)

        if not name and not email and not customer_id:
            return self._format_response(
                total=0,
                errors=[{"service": "customer", "error": "Provide name, email, or id"}],
                matches=[],
                primary=None,
                match_count=0,
            )

        # Determine which services to search
        service_map = CUSTOMER_SERVICES.copy()
        if services_filter:
            service_map = {k: v for k, v in service_map.items() if k in services_filter}

        # Get available services
        available = self._get_connected_services(org_id, user_id, service_map)

        if not available:
            return self._format_response(
                total=0,
                errors=[{"service": "customer", "error": "No customer services connected"}],
                matches=[],
                primary=None,
                match_count=0,
            )

        matches: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        sources: list[str] = []

        # Handle ID lookup (direct service call)
        if customer_id and ":" in customer_id:
            service_prefix, entity_id = customer_id.split(":", 1)
            if service_prefix in available:
                result = self._lookup_customer_by_id(org_id, user_id, service_prefix, entity_id)
                if result:
                    matches.append(result)
                    sources.append(service_prefix)

        # Search by name/email across services
        else:
            for service in available:
                try:
                    service_matches = self._search_customers_in_service(
                        org_id, user_id, service, name, email, fuzzy
                    )
                    matches.extend(service_matches)
                    if service_matches:
                        sources.append(service)
                except Exception as e:
                    logger.warning(
                        "Customer search failed",
                        service=service,
                        error=str(e),
                        log_event="fci_customer_search_error",
                    )
                    errors.append(
                        {
                            "service": service,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    )

        # Sort matches by confidence and pick primary
        matches.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        primary = matches[0] if matches else None

        return self._format_response(
            total=len(matches),
            sources=sources,
            errors=errors if errors else None,
            matches=matches,
            primary=primary,
            match_count=len(matches),
        )

    def lookup_vendor(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Look up a vendor across all connected services.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - name: Vendor name to search (partial/fuzzy)
                - email: Vendor email (exact match preferred)
                - id: Vendor ID with service prefix (e.g., 'qb:123', 'billcom:xxx')
                - services: Limit search to specific services (list)
                - fuzzy: Enable fuzzy name matching (default: False)

        Returns:
            {
                "matches": [{service, id, name, email, confidence}],
                "primary": {service, id, name, balance, last_payment},
                "match_count": int,
                "lastUpdated": str,
                "sources": [str],
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        name = args.get("name")
        email = args.get("email")
        vendor_id = args.get("id")
        services_filter = args.get("services", [])
        fuzzy = args.get("fuzzy", False)

        if not name and not email and not vendor_id:
            return self._format_response(
                total=0,
                errors=[{"service": "vendor", "error": "Provide name, email, or id"}],
                matches=[],
                primary=None,
                match_count=0,
            )

        service_map = VENDOR_SERVICES.copy()
        if services_filter:
            service_map = {k: v for k, v in service_map.items() if k in services_filter}

        available = self._get_connected_services(org_id, user_id, service_map)

        if not available:
            return self._format_response(
                total=0,
                errors=[{"service": "vendor", "error": "No vendor services connected"}],
                matches=[],
                primary=None,
                match_count=0,
            )

        matches: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        sources: list[str] = []

        if vendor_id and ":" in vendor_id:
            service_prefix, entity_id = vendor_id.split(":", 1)
            if service_prefix in available:
                result = self._lookup_vendor_by_id(org_id, user_id, service_prefix, entity_id)
                if result:
                    matches.append(result)
                    sources.append(service_prefix)
        else:
            for service in available:
                try:
                    service_matches = self._search_vendors_in_service(
                        org_id, user_id, service, name, email, fuzzy
                    )
                    matches.extend(service_matches)
                    if service_matches:
                        sources.append(service)
                except Exception as e:
                    logger.warning(
                        "Vendor search failed",
                        service=service,
                        error=str(e),
                        log_event="fci_vendor_search_error",
                    )
                    errors.append(
                        {
                            "service": service,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    )

        matches.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        primary = matches[0] if matches else None

        return self._format_response(
            total=len(matches),
            sources=sources,
            errors=errors if errors else None,
            matches=matches,
            primary=primary,
            match_count=len(matches),
        )

    def lookup_invoice(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Look up an invoice across all connected services.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - invoice_number: Customer-facing invoice number
                - id: Internal invoice ID with service prefix
                - customer_name: Filter by customer name
                - services: Limit search to specific services (list)

        Returns:
            {
                "matches": [{service, id, number, customer, amount, status}],
                "primary": {full invoice details},
                "match_count": int,
                "lastUpdated": str,
                "sources": [str],
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        invoice_number = args.get("invoice_number")
        invoice_id = args.get("id")
        customer_name = args.get("customer_name")
        services_filter = args.get("services", [])

        if not invoice_number and not invoice_id:
            return self._format_response(
                total=0,
                errors=[{"service": "invoice", "error": "Provide invoice_number or id"}],
                matches=[],
                primary=None,
                match_count=0,
            )

        service_map = INVOICE_SERVICES.copy()
        if services_filter:
            service_map = {k: v for k, v in service_map.items() if k in services_filter}

        available = self._get_connected_services(org_id, user_id, service_map)

        if not available:
            return self._format_response(
                total=0,
                errors=[{"service": "invoice", "error": "No invoice services connected"}],
                matches=[],
                primary=None,
                match_count=0,
            )

        matches: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        sources: list[str] = []

        if invoice_id and ":" in invoice_id:
            service_prefix, entity_id = invoice_id.split(":", 1)
            if service_prefix in available:
                result = self._lookup_invoice_by_id(org_id, user_id, service_prefix, entity_id)
                if result:
                    matches.append(result)
                    sources.append(service_prefix)
        else:
            for service in available:
                try:
                    service_matches = self._search_invoices_in_service(
                        org_id, user_id, service, invoice_number, customer_name
                    )
                    matches.extend(service_matches)
                    if service_matches:
                        sources.append(service)
                except Exception as e:
                    logger.warning(
                        "Invoice search failed",
                        service=service,
                        error=str(e),
                        log_event="fci_invoice_search_error",
                    )
                    errors.append(
                        {
                            "service": service,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    )

        matches.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        primary = matches[0] if matches else None

        return self._format_response(
            total=len(matches),
            sources=sources,
            errors=errors if errors else None,
            matches=matches,
            primary=primary,
            match_count=len(matches),
        )

    # =========================================================================
    # Service-specific lookup helpers
    # =========================================================================

    def _lookup_customer_by_id(
        self,
        org_id: str,
        user_id: str,
        service: str,
        entity_id: str,
    ) -> dict[str, Any] | None:
        """Look up customer by ID in a specific service."""
        try:
            connector = self._get_connector(service)
            method = getattr(connector, CUSTOMER_SERVICES.get(service, "get_customer"), None)

            if not method:
                return None

            result = method(org_id, user_id, {"id": entity_id})

            return self._normalize_customer_result(service, result)
        except Exception as e:
            logger.warning(f"Customer ID lookup failed: {service}:{entity_id}", error=str(e))
            return None

    def _search_customers_in_service(
        self,
        org_id: str,
        user_id: str,
        service: str,
        name: str | None,
        email: str | None,
        fuzzy: bool,
    ) -> list[dict[str, Any]]:
        """Search for customers in a specific service."""
        matches: list[dict[str, Any]] = []

        try:
            connector = self._get_connector(service)

            # Build search query
            search_args: dict[str, Any] = {}
            if name:
                search_args["name"] = name
                search_args["query"] = name
            if email:
                search_args["email"] = email

            # Different services have different search methods
            if service == "quickbooks":
                # QB uses query language
                if name:
                    sanitized_name = _sanitize_qboql(name)
                    search_args["query"] = (
                        f"SELECT * FROM Customer WHERE DisplayName LIKE '%{sanitized_name}%'"
                    )
                method = getattr(connector, "query_entities", None)
            elif service == "stripe":
                method = getattr(
                    connector, "search_customers", getattr(connector, "list_customers", None)
                )
            elif service == "hubspot":
                method = getattr(
                    connector, "search_contacts", getattr(connector, "list_contacts", None)
                )
            else:
                method = getattr(
                    connector, "list_customers", getattr(connector, "get_customers", None)
                )

            if not method:
                return matches

            result = method(org_id, user_id, search_args)

            # Parse results
            qr = result.get("QueryResponse", {})
            customers = result.get(
                "customers", result.get("contacts", result.get("results", qr.get("Customer", [])))
            )

            if isinstance(customers, list):
                for cust in customers:
                    normalized = self._normalize_customer_result(service, cust)
                    if normalized:
                        # Calculate confidence
                        confidence = self._calculate_match_confidence(
                            normalized, name, email, fuzzy
                        )
                        normalized["confidence"] = confidence
                        if confidence > 0:
                            matches.append(normalized)

        except Exception as e:
            logger.debug(f"Customer search in {service} failed: {e}")

        return matches

    def _lookup_vendor_by_id(
        self,
        org_id: str,
        user_id: str,
        service: str,
        entity_id: str,
    ) -> dict[str, Any] | None:
        """Look up vendor by ID in a specific service."""
        try:
            connector = self._get_connector(service)
            method = getattr(connector, VENDOR_SERVICES.get(service, "get_vendor"), None)

            if not method:
                return None

            result = method(org_id, user_id, {"id": entity_id})

            return self._normalize_vendor_result(service, result)
        except Exception as e:
            logger.warning(f"Vendor ID lookup failed: {service}:{entity_id}", error=str(e))
            return None

    def _search_vendors_in_service(
        self,
        org_id: str,
        user_id: str,
        service: str,
        name: str | None,
        email: str | None,
        fuzzy: bool,
    ) -> list[dict[str, Any]]:
        """Search for vendors in a specific service."""
        matches: list[dict[str, Any]] = []

        try:
            connector = self._get_connector(service)

            search_args: dict[str, Any] = {}
            if name:
                search_args["name"] = name
            if email:
                search_args["email"] = email

            if service == "quickbooks":
                if name:
                    sanitized_name = _sanitize_qboql(name)
                    search_args["query"] = (
                        f"SELECT * FROM Vendor WHERE DisplayName LIKE '%{sanitized_name}%'"
                    )
                method = getattr(connector, "query_entities", None)
            else:
                method = getattr(connector, "list_vendors", getattr(connector, "get_vendors", None))

            if not method:
                return matches

            result = method(org_id, user_id, search_args)

            qr = result.get("QueryResponse", {})
            vendors = result.get("vendors", result.get("results", qr.get("Vendor", [])))

            if isinstance(vendors, list):
                for vendor in vendors:
                    normalized = self._normalize_vendor_result(service, vendor)
                    if normalized:
                        confidence = self._calculate_match_confidence(
                            normalized, name, email, fuzzy
                        )
                        normalized["confidence"] = confidence
                        if confidence > 0:
                            matches.append(normalized)

        except Exception as e:
            logger.debug(f"Vendor search in {service} failed: {e}")

        return matches

    def _lookup_invoice_by_id(
        self,
        org_id: str,
        user_id: str,
        service: str,
        entity_id: str,
    ) -> dict[str, Any] | None:
        """Look up invoice by ID in a specific service."""
        try:
            connector = self._get_connector(service)
            method = getattr(connector, INVOICE_SERVICES.get(service, "get_invoice"), None)

            if not method:
                return None

            result = method(org_id, user_id, {"id": entity_id})

            return self._normalize_invoice_result(service, result)
        except Exception as e:
            logger.warning(f"Invoice ID lookup failed: {service}:{entity_id}", error=str(e))
            return None

    def _search_invoices_in_service(
        self,
        org_id: str,
        user_id: str,
        service: str,
        invoice_number: str | None,
        customer_name: str | None,
    ) -> list[dict[str, Any]]:
        """Search for invoices in a specific service."""
        matches: list[dict[str, Any]] = []

        try:
            connector = self._get_connector(service)

            search_args: dict[str, Any] = {}
            if invoice_number:
                search_args["invoice_number"] = invoice_number
                search_args["doc_number"] = invoice_number

            if service == "quickbooks":
                if invoice_number:
                    sanitized_num = _sanitize_qboql(invoice_number)
                    search_args["query"] = (
                        f"SELECT * FROM Invoice WHERE DocNumber = '{sanitized_num}'"
                    )
                method = getattr(connector, "query_entities", None)
            else:
                method = getattr(
                    connector, "list_invoices", getattr(connector, "get_invoices", None)
                )

            if not method:
                return matches

            result = method(org_id, user_id, search_args)

            qr = result.get("QueryResponse", {})
            invoices = result.get("invoices", result.get("data", qr.get("Invoice", [])))

            if isinstance(invoices, list):
                for invoice in invoices:
                    normalized = self._normalize_invoice_result(service, invoice)
                    if normalized:
                        # Filter by customer name if provided
                        if customer_name:
                            inv_customer = normalized.get("customer", "").lower()
                            if customer_name.lower() not in inv_customer:
                                continue

                        normalized["confidence"] = 100 if invoice_number else 80
                        matches.append(normalized)

        except Exception as e:
            logger.debug(f"Invoice search in {service} failed: {e}")

        return matches

    # =========================================================================
    # Result normalization
    # =========================================================================

    def _normalize_customer_result(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Normalize customer result to standard format."""
        if not result:
            return None

        normalized = {
            "service": service,
            "id": f"{service}:",
            "name": "",
            "email": "",
            "confidence": 0,
        }

        if service == "quickbooks":
            normalized["id"] = f"qb:{result.get('Id', '')}"
            normalized["name"] = result.get("DisplayName", result.get("CompanyName", ""))
            normalized["email"] = result.get("PrimaryEmailAddr", {}).get("Address", "")
            normalized["balance"] = float(result.get("Balance", 0))

        elif service == "stripe":
            normalized["id"] = f"stripe:{result.get('id', '')}"
            normalized["name"] = result.get("name", "")
            normalized["email"] = result.get("email", "")

        elif service == "hubspot":
            normalized["id"] = f"hubspot:{result.get('id', '')}"
            props = result.get("properties", result)
            normalized["name"] = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            normalized["email"] = props.get("email", "")

        elif service == "shopify":
            normalized["id"] = f"shopify:{result.get('id', '')}"
            first = result.get("first_name", "")
            last = result.get("last_name", "")
            normalized["name"] = f"{first} {last}".strip()
            normalized["email"] = result.get("email", "")

        elif service == "square":
            normalized["id"] = f"square:{result.get('id', '')}"
            normalized["name"] = result.get("given_name", "") + " " + result.get("family_name", "")
            normalized["email"] = result.get("email_address", "")

        return normalized if normalized.get("name") or normalized.get("email") else None

    def _normalize_vendor_result(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Normalize vendor result to standard format."""
        if not result:
            return None

        normalized = {
            "service": service,
            "id": f"{service}:",
            "name": "",
            "email": "",
            "confidence": 0,
        }

        if service == "quickbooks":
            normalized["id"] = f"qb:{result.get('Id', '')}"
            normalized["name"] = result.get("DisplayName", result.get("CompanyName", ""))
            normalized["email"] = result.get("PrimaryEmailAddr", {}).get("Address", "")
            normalized["balance"] = float(result.get("Balance", 0))

        elif service == "xero":
            normalized["id"] = f"xero:{result.get('ContactID', '')}"
            normalized["name"] = result.get("Name", "")
            normalized["email"] = result.get("EmailAddress", "")

        elif service == "billcom":
            normalized["id"] = f"billcom:{result.get('id', '')}"
            normalized["name"] = result.get("name", "")
            normalized["email"] = result.get("email", "")

        elif service == "netsuite":
            normalized["id"] = f"netsuite:{result.get('id', '')}"
            normalized["name"] = result.get("companyName", result.get("entityId", ""))
            normalized["email"] = result.get("email", "")

        elif service == "sage_intacct":
            normalized["id"] = f"sage_intacct:{result.get('RECORDNO', result.get('VENDORID', ''))}"
            normalized["name"] = result.get("NAME", "")
            normalized["email"] = result.get("EMAIL1", "")

        return normalized if normalized.get("name") else None

    def _normalize_invoice_result(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Normalize invoice result to standard format."""
        if not result:
            return None

        normalized = {
            "service": service,
            "id": f"{service}:",
            "number": "",
            "customer": "",
            "amount": 0.0,
            "status": "",
            "confidence": 0,
        }

        if service == "quickbooks":
            normalized["id"] = f"qb:{result.get('Id', '')}"
            normalized["number"] = result.get("DocNumber", "")
            normalized["customer"] = result.get("CustomerRef", {}).get("name", "")
            normalized["amount"] = float(result.get("TotalAmt", 0))
            normalized["status"] = "paid" if result.get("Balance", 1) == 0 else "open"

        elif service == "xero":
            normalized["id"] = f"xero:{result.get('InvoiceID', '')}"
            normalized["number"] = result.get("InvoiceNumber", "")
            normalized["customer"] = result.get("Contact", {}).get("Name", "")
            normalized["amount"] = float(result.get("Total", 0))
            normalized["status"] = result.get("Status", "").lower()

        elif service == "stripe":
            normalized["id"] = f"stripe:{result.get('id', '')}"
            normalized["number"] = result.get("number", "")
            normalized["customer"] = result.get("customer_name", "")
            normalized["amount"] = float(result.get("amount_due", 0)) / 100
            normalized["status"] = result.get("status", "")

        return normalized if normalized.get("number") or normalized.get("id") else None

    def _calculate_match_confidence(
        self,
        normalized: dict[str, Any],
        search_name: str | None,
        search_email: str | None,
        fuzzy: bool,
    ) -> int:
        """Calculate match confidence score (0-100)."""
        confidence = 0

        entity_name = normalized.get("name", "").lower()
        entity_email = normalized.get("email", "").lower()

        # Email exact match is highest confidence
        if search_email and entity_email:
            if search_email.lower() == entity_email:
                confidence = 100
            elif search_email.lower() in entity_email:
                confidence = max(confidence, 90)

        # Name matching
        if search_name and entity_name:
            search_lower = search_name.lower()

            if search_lower == entity_name:
                confidence = max(confidence, 95)
            elif search_lower in entity_name or entity_name in search_lower:
                confidence = max(confidence, 80)
            elif fuzzy:
                # Simple fuzzy: check if all words in search appear in entity
                search_words = set(search_lower.split())
                entity_words = set(entity_name.split())
                overlap = len(search_words & entity_words)
                if overlap > 0:
                    confidence = max(confidence, int(60 * overlap / len(search_words)))

        return confidence
