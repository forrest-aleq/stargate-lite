"""
Gusto connector package

This package provides a modular Gusto API connector split across multiple files
to maintain code under the 500-line limit per file.

Modules:
- base: Authentication and token refresh
- company: Company operations
- employees: Employee operations
- payroll: Payroll operations
- contractors: Contractor operations
- tax_forms: Tax forms operations
"""

from app.connectors.gusto.base import GustoBase
from app.connectors.gusto.company import GustoCompanyMixin
from app.connectors.gusto.contractors import GustoContractorsMixin
from app.connectors.gusto.employees import GustoEmployeesMixin
from app.connectors.gusto.payroll import GustoPayrollMixin
from app.connectors.gusto.tax_forms import GustoTaxFormsMixin


class GustoConnector(
    GustoBase,
    GustoCompanyMixin,
    GustoEmployeesMixin,
    GustoPayrollMixin,
    GustoContractorsMixin,
    GustoTaxFormsMixin,
):
    """
    Gusto API connector.

    This class combines all Gusto operations through mixin classes:
    - Authentication and token management (from GustoBase)
    - Company operations (from GustoCompanyMixin)
    - Employee operations (from GustoEmployeesMixin)
    - Payroll operations (from GustoPayrollMixin)
    - Contractor operations (from GustoContractorsMixin)
    - Tax forms operations (from GustoTaxFormsMixin)
    """

    pass


# Singleton instance
gusto_connector = GustoConnector()

__all__ = ["GustoConnector", "gusto_connector"]
