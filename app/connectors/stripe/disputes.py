"""
Stripe connector - Disputes module

Handles dispute operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_init


class StripeDisputesMixin:
    """Stripe dispute operations mixin"""

    @requires_stripe_init
    def retrieve_dispute(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Retrieve a dispute"""
        dispute_id = args.get("dispute_id")
        if not dispute_id:
            raise ValueError("dispute_id is required")
        dispute = stripe.Dispute.retrieve(dispute_id)
        return {
            "dispute_id": dispute.id,
            "amount": dispute.amount,
            "currency": dispute.currency,
            "status": dispute.status,
            "reason": dispute.reason,
            "charge": dispute.charge,
        }

    @requires_stripe_init
    def update_dispute(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a dispute (submit evidence)"""
        dispute_id = args.get("dispute_id")
        if not dispute_id:
            raise ValueError("dispute_id is required")
        evidence = args.get("evidence", {})
        metadata = args.get("metadata", {})

        update_params: dict[str, Any] = {}
        if evidence:
            update_params["evidence"] = evidence
        if metadata:
            update_params["metadata"] = metadata

        dispute = stripe.Dispute.modify(dispute_id, **update_params)
        return {"dispute_id": dispute.id, "status": dispute.status}

    @requires_stripe_init
    def close_dispute(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Close a dispute (accept the dispute)"""
        dispute_id = args.get("dispute_id")
        if not dispute_id:
            raise ValueError("dispute_id is required")
        dispute = stripe.Dispute.close(dispute_id)
        return {"dispute_id": dispute.id, "status": dispute.status}

    @requires_stripe_init
    def list_disputes(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List disputes"""
        limit = args.get("limit", 10)
        charge = args.get("charge_id")

        params: dict[str, Any] = {"limit": limit}
        if charge:
            params["charge"] = charge

        disputes = stripe.Dispute.list(**params)
        return {
            "disputes": [
                {
                    "dispute_id": d.id,
                    "amount": d.amount,
                    "status": d.status,
                    "reason": d.reason,
                    "charge": d.charge,
                }
                for d in disputes.data
            ],
            "has_more": disputes.has_more,
        }
