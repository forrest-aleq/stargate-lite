from pathlib import Path

from scripts import check_railway_readiness as readiness


def test_load_customer_connect_requirements_from_constants() -> None:
    requirements = readiness._load_customer_connect_requirements(Path("app/constants/services.py"))

    assert requirements["quickbooks"] == (
        "QUICKBOOKS_CLIENT_ID",
        "QUICKBOOKS_CLIENT_SECRET",
        "QUICKBOOKS_REDIRECT_URI",
    )
    assert requirements["stripe"] == (
        "STRIPE_SECRET_KEY",
        "STRIPE_CLIENT_ID",
        "STRIPE_REDIRECT_URI",
    )


def test_missing_customer_connect_vars_requires_full_provider_env_set() -> None:
    requirements = {
        "quickbooks": (
            "QUICKBOOKS_CLIENT_ID",
            "QUICKBOOKS_CLIENT_SECRET",
            "QUICKBOOKS_REDIRECT_URI",
        ),
        "stripe": (
            "STRIPE_SECRET_KEY",
            "STRIPE_CLIENT_ID",
            "STRIPE_REDIRECT_URI",
        ),
    }

    missing = readiness._missing_customer_connect_vars(
        {
            "QUICKBOOKS_CLIENT_ID": "set",
            "QUICKBOOKS_CLIENT_SECRET": "set",
            "STRIPE_SECRET_KEY": "set",
        },
        ["quickbooks", "stripe"],
        requirements,
    )

    assert missing == [
        "quickbooks:QUICKBOOKS_REDIRECT_URI",
        "stripe:STRIPE_CLIENT_ID",
        "stripe:STRIPE_REDIRECT_URI",
    ]


def test_railway_readiness_requires_control_plane_runtime_vars() -> None:
    assert "CONTROL_PLANE_API_KEY" in readiness.CORE_REQUIRED_VARS
    assert "CONTROL_PLANE_BASE_URL" in readiness.CORE_REQUIRED_VARS
