"""
Authentication utilities for Stargate Lite.
"""

import os
import secrets

from fastapi import Header, HTTPException

API_SECRET_KEY = os.getenv("API_SECRET_KEY")


def verify_api_key(x_api_key: str | None = Header(None)) -> bool:
    """Verify the internal API key"""
    if not API_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="API_SECRET_KEY environment variable is not configured",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, API_SECRET_KEY):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True
