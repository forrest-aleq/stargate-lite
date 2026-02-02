"""
OAuth Routes Package

This package provides OAuth flows for all integrated services, split by category:
- quickbooks: QuickBooks Online accounting
- hubspot: HubSpot CRM
- google: Google Workspace (Gmail, Drive, Calendar, Sheets)
- slack: Slack messaging
- microsoft: Microsoft 365 (Excel, OneDrive, Outlook, Power BI)
- netsuite: NetSuite ERP
- fintech: Brex, Ramp, Chase, Schwab
- task_managers: Asana, ClickUp, Monday.com
- notes_issues: Notion, Linear
- hr_payroll: Gusto
- ecommerce: Shopify, Square
- esignature: DocuSign
- productivity_db: Airtable
- stripe: Stripe Connect (payments)
- xero: Xero Accounting
"""

from fastapi import APIRouter

from app.routers.oauth.ecommerce import router as ecommerce_router
from app.routers.oauth.esignature import router as esignature_router
from app.routers.oauth.fintech import router as fintech_router
from app.routers.oauth.google import router as google_router
from app.routers.oauth.hr_payroll import router as hr_payroll_router
from app.routers.oauth.hubspot import router as hubspot_router
from app.routers.oauth.microsoft import router as microsoft_router
from app.routers.oauth.netsuite import router as netsuite_router
from app.routers.oauth.notes_issues import router as notes_issues_router
from app.routers.oauth.productivity_db import router as productivity_db_router
from app.routers.oauth.quickbooks import router as quickbooks_router
from app.routers.oauth.slack import router as slack_router
from app.routers.oauth.stripe import router as stripe_router
from app.routers.oauth.task_managers import router as task_managers_router
from app.routers.oauth.xero import router as xero_router

# Create combined router
router = APIRouter(tags=["oauth"])

# Include all OAuth sub-routers
router.include_router(quickbooks_router)
router.include_router(hubspot_router)
router.include_router(google_router)
router.include_router(slack_router)
router.include_router(microsoft_router)
router.include_router(netsuite_router)
router.include_router(fintech_router)
router.include_router(task_managers_router)
router.include_router(notes_issues_router)
router.include_router(hr_payroll_router)
router.include_router(ecommerce_router)
router.include_router(esignature_router)
router.include_router(productivity_db_router)
router.include_router(stripe_router)
router.include_router(xero_router)

__all__ = ["router"]
