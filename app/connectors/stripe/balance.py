"""
Stripe connector - Balance module

Handles balance, payouts, and transfers.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_config
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeBalanceMixin:
    """Stripe balance and payout operations mixin"""

    @requires_stripe_config
    def get_balance(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get current Stripe balance"""
        logger.info("Retrieving balance", service="stripe", log_event="stripe_balance_retrieve")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        balance = stripe.Balance.retrieve(**retrieve_kwargs)

        total_available = sum(bal.amount for bal in balance.available)
        total_pending = sum(bal.amount for bal in balance.pending)

        logger.info(
            "Balance retrieved",
            service="stripe",
            total_available=total_available,
            total_pending=total_pending,
            log_event="stripe_balance_retrieved",
        )

        return {
            "available": [
                {"amount": bal.amount, "currency": bal.currency} for bal in balance.available
            ],
            "pending": [
                {"amount": bal.amount, "currency": bal.currency} for bal in balance.pending
            ],
            "connect_reserved": balance.get("connect_reserved", []),
        }

    @requires_stripe_config
    def list_payouts(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List Stripe payouts"""
        limit = args.get("limit", 10)
        status = args.get("status")

        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

        payouts = stripe.Payout.list(**params)
        return {
            "payouts": [
                {
                    "payout_id": p.id,
                    "amount": p.amount,
                    "currency": p.currency,
                    "status": p.status,
                    "arrival_date": p.arrival_date,
                }
                for p in payouts.data
            ],
            "has_more": payouts.has_more,
        }

    @requires_stripe_config
    def retrieve_payout(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a specific payout"""
        payout_id = args.get("payout_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        payout = stripe.Payout.retrieve(payout_id, **retrieve_kwargs)
        return {
            "payout_id": payout.id,
            "amount": payout.amount,
            "currency": payout.currency,
            "status": payout.status,
            "arrival_date": payout.arrival_date,
            "destination": payout.destination,
        }

    @requires_stripe_config
    def list_balance_transactions(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List balance transactions"""
        limit = args.get("limit", 10)
        payout = args.get("payout_id")
        type_ = args.get("type")

        params: dict[str, Any] = {"limit": limit}
        if payout:
            params["payout"] = payout
        if type_:
            params["type"] = type_
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

        transactions = stripe.BalanceTransaction.list(**params)
        return {
            "transactions": [
                {
                    "id": t.id,
                    "amount": t.amount,
                    "currency": t.currency,
                    "type": t.type,
                    "net": t.net,
                    "created": t.created,
                }
                for t in transactions.data
            ],
            "has_more": transactions.has_more,
        }

    @requires_stripe_config
    def create_transfer(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a transfer (Connect accounts)"""
        amount = args.get("amount")
        currency = args.get("currency", "usd")
        destination = args.get("destination")  # Connected account ID
        description = args.get("description")
        metadata = args.get("metadata", {})

        logger.info(
            "Creating transfer",
            service="stripe",
            amount=amount,
            destination=destination,
            log_event="stripe_transfer_create",
        )

        metadata.update({"org_id": org_id, "user_id": user_id})

        transfer_params: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "destination": destination,
            "description": description,
            "metadata": metadata,
        }
        if stripe_config and stripe_config.get("stripe_account"):
            transfer_params["stripe_account"] = stripe_config["stripe_account"]

        transfer = stripe.Transfer.create(**transfer_params)

        logger.info(
            "Transfer created",
            service="stripe",
            transfer_id=transfer.id,
            amount=transfer.amount,
            log_event="stripe_transfer_created",
        )

        return {
            "transfer_id": transfer.id,
            "amount": transfer.amount,
            "currency": transfer.currency,
            "destination": transfer.destination,
        }

    @requires_stripe_config
    def list_transfers(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List transfers"""
        limit = args.get("limit", 10)
        destination = args.get("destination")

        params: dict[str, Any] = {"limit": limit}
        if destination:
            params["destination"] = destination
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

        transfers = stripe.Transfer.list(**params)
        return {
            "transfers": [
                {
                    "transfer_id": t.id,
                    "amount": t.amount,
                    "currency": t.currency,
                    "destination": t.destination,
                    "created": t.created,
                }
                for t in transfers.data
            ],
            "has_more": transfers.has_more,
        }

    @requires_stripe_config
    def retrieve_balance_transaction(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a specific balance transaction"""
        txn_id = args.get("balance_transaction_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        txn = stripe.BalanceTransaction.retrieve(txn_id, **retrieve_kwargs)
        return {
            "id": txn.id,
            "amount": txn.amount,
            "currency": txn.currency,
            "type": txn.type,
            "net": txn.net,
            "fee": txn.fee,
            "status": txn.status,
            "created": txn.created,
            "source": txn.source,
            "description": txn.description,
        }

    @requires_stripe_config
    def create_payout(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a payout to a bank account or debit card"""
        amount = args.get("amount")
        currency = args.get("currency", "usd")
        description = args.get("description")
        destination = args.get("destination")
        metadata = args.get("metadata", {})

        logger.info(
            "Creating payout",
            service="stripe",
            amount=amount,
            currency=currency,
            log_event="stripe_payout_create",
        )

        metadata.update({"org_id": org_id, "user_id": user_id})

        payout_params: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "metadata": metadata,
        }
        if description:
            payout_params["description"] = description
        if destination:
            payout_params["destination"] = destination
        if stripe_config and stripe_config.get("stripe_account"):
            payout_params["stripe_account"] = stripe_config["stripe_account"]

        payout = stripe.Payout.create(**payout_params)

        logger.info(
            "Payout created",
            service="stripe",
            payout_id=payout.id,
            amount=payout.amount,
            log_event="stripe_payout_created",
        )

        return {
            "payout_id": payout.id,
            "amount": payout.amount,
            "currency": payout.currency,
            "status": payout.status,
            "arrival_date": payout.arrival_date,
        }
