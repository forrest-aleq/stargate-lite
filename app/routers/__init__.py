"""
Routers package for Stargate Lite.

Contains all API route modules:
- health: Health check routes (/, /health, /health/connectors)
- connectors: Workflow connector status (/api/v1/connectors/status)
- credentials: Credential and capability routes (/api/v1/credentials/*, /api/v1/capabilities)
- execute: Tool execution route (/api/v1/execute)
- oauth: OAuth callback routes for various services
- schemas: Schema discovery routes (/api/v1/schemas/*, /api/v1/services)
"""

from app.routers import connectors, credentials, execute, health, schemas
from app.routers.oauth import router as oauth_router

__all__ = ["connectors", "credentials", "execute", "health", "oauth_router", "schemas"]
