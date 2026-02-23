"""
Zoho Books parity tests.

Validates that the generated manifest and capability registry stay aligned.
"""

from app.connectors.zoho_books import get_operation_count, get_operations
from app.constants.services import ALL_SERVICES_OAUTH, OAUTH_AUTHORIZE_PATHS, SERVICE_DISPLAY_NAMES
from app.registry.financial.zoho_books import ZOHO_BOOKS_CAPABILITIES


def test_zoho_books_manifest_has_full_surface_area() -> None:
    # OpenAPI bundle (Feb 4, 2026) contains 529 operations.
    # Keep this threshold high to catch accidental truncation/regressions.
    assert get_operation_count() >= 500
    assert get_operation_count() == len(get_operations())


def test_zoho_books_registry_matches_manifest() -> None:
    assert len(ZOHO_BOOKS_CAPABILITIES) == get_operation_count()

    for capability_key, config in ZOHO_BOOKS_CAPABILITIES.items():
        assert capability_key.startswith("zoho_books.")
        assert config["service"] == "zoho_books"
        assert config["requires_oauth"] is True
        assert callable(config["handler"])


def test_zoho_books_service_constants_are_wired() -> None:
    assert ALL_SERVICES_OAUTH["zoho_books"] is True
    assert SERVICE_DISPLAY_NAMES["zoho_books"] == "Zoho Books"
    assert OAUTH_AUTHORIZE_PATHS["zoho_books"] == "/oauth/zoho_books/authorize"
