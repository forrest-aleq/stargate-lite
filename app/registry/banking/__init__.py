"""
Banking/Payments Capability Registry
Plaid, Ramp, Mercury, Brex, Chase
"""

from app.registry.banking.brex import BREX_CAPABILITIES
from app.registry.banking.chase import CHASE_CAPABILITIES
from app.registry.banking.mercury import MERCURY_CAPABILITIES
from app.registry.banking.plaid import PLAID_CAPABILITIES
from app.registry.banking.ramp import RAMP_CAPABILITIES

BANKING_CAPABILITIES = {
    **PLAID_CAPABILITIES,
    **RAMP_CAPABILITIES,
    **MERCURY_CAPABILITIES,
    **BREX_CAPABILITIES,
    **CHASE_CAPABILITIES,
}
