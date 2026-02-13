"""
Authentication utilities for Stargate Lite.

Validates API key and optional HMAC-SHA256 request signatures.
Baby MARS sends X-API-Key, X-Timestamp, and X-Signature-256 on every request.
"""

import hashlib
import hmac
import os
import secrets
import time

from fastapi import Header, HTTPException, Request

API_SECRET_KEY = os.getenv("API_SECRET_KEY")

# Reject requests with timestamps older than 5 minutes (replay protection)
SIGNATURE_TOLERANCE_SECONDS = 300


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(None),
    x_timestamp: str | None = Header(None, alias="X-Timestamp"),
    x_signature_256: str | None = Header(None, alias="X-Signature-256"),
) -> bool:
    """Verify API key and optional HMAC-SHA256 request signature.

    When X-Timestamp and X-Signature-256 headers are present, validates:
    1. Timestamp is within 5 minutes of server time (replay protection)
    2. HMAC-SHA256(body) matches the signature (tamper protection)
    """
    if not API_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="API_SECRET_KEY environment variable is not configured",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, API_SECRET_KEY):
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # Validate HMAC signature when both headers are present
    if x_timestamp is not None and x_signature_256 is not None:
        try:
            ts = int(x_timestamp)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid X-Timestamp header") from exc

        if abs(int(time.time()) - ts) > SIGNATURE_TOLERANCE_SECONDS:
            raise HTTPException(status_code=403, detail="Request timestamp expired")

        body = await request.body()
        expected = hmac.new(API_SECRET_KEY.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(x_signature_256, expected):
            raise HTTPException(status_code=403, detail="Invalid request signature")

    return True
