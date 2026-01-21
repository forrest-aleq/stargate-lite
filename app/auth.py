"""
Authentication utilities for Stargate Lite.
"""

import os

from fastapi import Header, HTTPException

API_SECRET_KEY = os.getenv("API_SECRET_KEY")


def verify_api_key(x_api_key: str | None = Header(None)) -> bool:
    """Verify the internal API key"""
    if not API_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="API_SECRET_KEY environment variable is not configured",
        )
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True
