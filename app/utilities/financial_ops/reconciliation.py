"""
Bank Reconciliation Engine for Financial Operations utility.

Matches GL transactions against bank transactions to identify:
- Matched items (exact, aggregate, timing)
- Unmatched GL items (not in bank)
- Unmatched bank items (not in GL)
- Variance analysis
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .base import FinancialOpsBase

logger = get_logger(__name__)


class MatchType(str, Enum):
    """Types of transaction matches."""

    EXACT = "exact"
    AMOUNT_ONLY = "amount_only"
    AGGREGATE = "aggregate"
    TIMING = "timing"
    REVERSAL = "reversal"


class ReconciliationMixin(FinancialOpsBase):
    """Mixin providing bank reconciliation capabilities."""

    def reconcile_transactions(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Reconcile GL transactions against bank transactions."""
        self._ensure_initialized()

        gl_transactions, bank_transactions, tolerance, date_window, as_of_date = (
            self._validate_reconcile_args(args)
        )

        gl_items = self._normalize_transactions(gl_transactions, "gl")
        bank_items = self._normalize_transactions(bank_transactions, "bank")

        matched, gl_matched_ids, bank_matched_ids = self._perform_matching(
            gl_items, bank_items, tolerance, date_window
        )

        gl_unmatched = [g["original"] for g in gl_items if g["id"] not in gl_matched_ids]
        bank_unmatched = [b["original"] for b in bank_items if b["id"] not in bank_matched_ids]

        timing_items = self._find_timing_items(gl_items, gl_matched_ids, as_of_date, date_window)

        summary = self._build_reconcile_summary(
            gl_items, bank_items, matched, gl_unmatched, bank_unmatched, timing_items
        )

        logger.info(
            "Bank reconciliation completed",
            service=self.SERVICE_NAME,
            gl_count=len(gl_items),
            bank_count=len(bank_items),
            matched_count=len(matched),
            match_rate=summary["match_rate"],
            log_event="reconciliation_complete",
        )
        self._track_usage()

        return {
            "matched": matched,
            "gl_unmatched": gl_unmatched,
            "bank_unmatched": bank_unmatched,
            "timing_items": timing_items,
            "summary": summary,
            "status": "success",
        }

    def _validate_reconcile_args(
        self, args: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Decimal, int, datetime]:
        """Validate and extract reconciliation arguments."""
        gl_transactions = args.get("gl_transactions")
        if not gl_transactions or not isinstance(gl_transactions, list):
            raise ValidationError("gl_transactions", "List of GL transactions required")

        bank_transactions = args.get("bank_transactions")
        if not bank_transactions or not isinstance(bank_transactions, list):
            raise ValidationError("bank_transactions", "List of bank transactions required")

        tolerance = Decimal(str(args.get("tolerance", 0.01)))
        date_window = int(args.get("date_window", 3))
        as_of_date_str = args.get("as_of_date")
        if as_of_date_str:
            as_of_date = datetime.fromisoformat(as_of_date_str)
            # Ensure timezone-aware
            if as_of_date.tzinfo is None:
                as_of_date = as_of_date.replace(tzinfo=UTC)
        else:
            as_of_date = datetime.now(UTC)
        return gl_transactions, bank_transactions, tolerance, date_window, as_of_date

    def _perform_matching(
        self,
        gl_items: list[dict[str, Any]],
        bank_items: list[dict[str, Any]],
        tolerance: Decimal,
        date_window: int,
    ) -> tuple[list[dict[str, Any]], set[str], set[str]]:
        """Perform all matching phases and return results."""
        matched: list[dict[str, Any]] = []
        gl_matched_ids: set[str] = set()
        bank_matched_ids: set[str] = set()

        # Phase 1: Exact matches
        self._match_exact(
            gl_items, bank_items, tolerance, matched, gl_matched_ids, bank_matched_ids
        )

        # Phase 2: Amount-only matches
        self._match_amount_only(
            gl_items, bank_items, tolerance, date_window, matched, gl_matched_ids, bank_matched_ids
        )

        # Phase 3: Aggregate matches
        unmatched_gl = [g for g in gl_items if g["id"] not in gl_matched_ids]
        unmatched_bank = [b for b in bank_items if b["id"] not in bank_matched_ids]
        aggregate_matches = self._find_aggregate_matches(
            unmatched_gl, unmatched_bank, tolerance, date_window
        )
        for agg_match in aggregate_matches:
            matched.append(agg_match)
            for gl_id in agg_match["gl_ids"]:
                gl_matched_ids.add(gl_id)
            bank_matched_ids.add(agg_match["bank_id"])

        return matched, gl_matched_ids, bank_matched_ids

    def _match_exact(
        self,
        gl_items: list[dict[str, Any]],
        bank_items: list[dict[str, Any]],
        tolerance: Decimal,
        matched: list[dict[str, Any]],
        gl_matched_ids: set[str],
        bank_matched_ids: set[str],
    ) -> None:
        """Phase 1: Find exact matches (same amount, same date)."""
        for gl in gl_items:
            if gl["id"] in gl_matched_ids:
                continue
            for bank in bank_items:
                if bank["id"] in bank_matched_ids:
                    continue
                if self._is_exact_match(gl, bank, tolerance):
                    matched.append(
                        {
                            "gl_txn": gl["original"],
                            "bank_txn": bank["original"],
                            "match_type": MatchType.EXACT.value,
                            "confidence": 1.0,
                            "gl_amount": float(gl["amount"]),
                            "bank_amount": float(bank["amount"]),
                        }
                    )
                    gl_matched_ids.add(gl["id"])
                    bank_matched_ids.add(bank["id"])
                    break

    def _match_amount_only(
        self,
        gl_items: list[dict[str, Any]],
        bank_items: list[dict[str, Any]],
        tolerance: Decimal,
        date_window: int,
        matched: list[dict[str, Any]],
        gl_matched_ids: set[str],
        bank_matched_ids: set[str],
    ) -> None:
        """Phase 2: Find amount-only matches within date window."""
        for gl in gl_items:
            if gl["id"] in gl_matched_ids:
                continue
            for bank in bank_items:
                if bank["id"] in bank_matched_ids:
                    continue
                if self._is_amount_match(gl, bank, tolerance, date_window):
                    days_diff = abs((gl["date"] - bank["date"]).days)
                    confidence = 1.0 - (days_diff / (date_window + 1)) * 0.2
                    matched.append(
                        {
                            "gl_txn": gl["original"],
                            "bank_txn": bank["original"],
                            "match_type": MatchType.AMOUNT_ONLY.value,
                            "confidence": round(confidence, 2),
                            "gl_amount": float(gl["amount"]),
                            "bank_amount": float(bank["amount"]),
                            "days_difference": days_diff,
                        }
                    )
                    gl_matched_ids.add(gl["id"])
                    bank_matched_ids.add(bank["id"])
                    break

    def _find_timing_items(
        self,
        gl_items: list[dict[str, Any]],
        gl_matched_ids: set[str],
        as_of_date: datetime,
        date_window: int,
    ) -> list[dict[str, Any]]:
        """Find timing items (GL has it, bank doesn't yet)."""
        cutoff = as_of_date - timedelta(days=date_window)
        return [
            {
                "transaction": gl["original"],
                "amount": float(gl["amount"]),
                "days_outstanding": (as_of_date - gl["date"]).days,
            }
            for gl in gl_items
            if gl["id"] not in gl_matched_ids and gl["date"] >= cutoff
        ]

    def _build_reconcile_summary(
        self,
        gl_items: list[dict[str, Any]],
        bank_items: list[dict[str, Any]],
        matched: list[dict[str, Any]],
        gl_unmatched: list[dict[str, Any]],
        bank_unmatched: list[dict[str, Any]],
        timing_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build reconciliation summary statistics."""
        gl_total = sum((g["amount"] for g in gl_items), Decimal("0"))
        bank_total = sum((b["amount"] for b in bank_items), Decimal("0"))
        matched_gl_total = sum(
            (Decimal(str(m.get("gl_amount", 0))) for m in matched if "gl_amount" in m),
            Decimal("0"),
        )
        matched_bank_total = sum(
            (Decimal(str(m.get("bank_amount", 0))) for m in matched if "bank_amount" in m),
            Decimal("0"),
        )

        return {
            "gl_total": float(gl_total.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "bank_total": float(bank_total.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "variance": float((gl_total - bank_total).quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "gl_transaction_count": len(gl_items),
            "bank_transaction_count": len(bank_items),
            "matched_count": len(matched),
            "gl_unmatched_count": len(gl_unmatched),
            "bank_unmatched_count": len(bank_unmatched),
            "match_rate": round(len(matched) / max(len(gl_items), 1) * 100, 1),
            "timing_items_count": len(timing_items),
            "matched_gl_total": float(matched_gl_total.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "matched_bank_total": float(
                matched_bank_total.quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
        }

    def _normalize_transactions(
        self, transactions: list[dict[str, Any]], source: str
    ) -> list[dict[str, Any]]:
        """Normalize transactions to common format for matching."""
        normalized = []
        for i, txn in enumerate(transactions):
            txn_id = txn.get("id", f"{source}_{i}")
            date_val = txn.get("date")
            if isinstance(date_val, str):
                date_val = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            elif not isinstance(date_val, datetime):
                date_val = datetime.now(UTC)
            # Ensure timezone-aware
            if date_val.tzinfo is None:
                date_val = date_val.replace(tzinfo=UTC)

            normalized.append(
                {
                    "id": str(txn_id),
                    "date": date_val,
                    "amount": Decimal(str(txn.get("amount", 0))),
                    "description": txn.get("description", ""),
                    "reference": txn.get("reference", ""),
                    "original": txn,
                }
            )
        return normalized

    def _is_exact_match(self, gl: dict[str, Any], bank: dict[str, Any], tolerance: Decimal) -> bool:
        """Check if two transactions are exact matches."""
        amount_diff = abs(gl["amount"] - bank["amount"])
        date_diff = abs((gl["date"] - bank["date"]).days)
        return bool(amount_diff <= tolerance and date_diff == 0)

    def _is_amount_match(
        self, gl: dict[str, Any], bank: dict[str, Any], tolerance: Decimal, date_window: int
    ) -> bool:
        """Check if two transactions match by amount within date window."""
        amount_diff = abs(gl["amount"] - bank["amount"])
        date_diff = abs((gl["date"] - bank["date"]).days)
        return bool(amount_diff <= tolerance and date_diff <= date_window)

    def _find_aggregate_matches(
        self,
        gl_items: list[dict[str, Any]],
        bank_items: list[dict[str, Any]],
        tolerance: Decimal,
        date_window: int,
    ) -> list[dict[str, Any]]:
        """Find cases where multiple GL items sum to one bank item."""
        matches: list[dict[str, Any]] = []
        gl_by_date: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for gl in gl_items:
            gl_by_date[gl["date"].date()].append(gl)

        for bank in bank_items:
            if bank["amount"] <= 0:
                continue
            match = self._try_aggregate_match(bank, gl_by_date, tolerance, date_window)
            if match:
                matches.append(match)
        return matches

    def _try_aggregate_match(
        self,
        bank: dict[str, Any],
        gl_by_date: dict[Any, list[dict[str, Any]]],
        tolerance: Decimal,
        date_window: int,
    ) -> dict[str, Any] | None:
        """Try to find aggregate match for a single bank transaction."""
        bank_date = bank["date"].date()
        candidate_gl = []
        for delta in range(-date_window, date_window + 1):
            check_date = bank_date + timedelta(days=delta)
            candidate_gl.extend(gl_by_date.get(check_date, []))

        candidate_gl = [g for g in candidate_gl if g["amount"] > 0]
        if not candidate_gl:
            return None

        sorted_gl = sorted(candidate_gl, key=lambda x: x["amount"], reverse=True)
        selected, running_total = [], Decimal("0")

        for gl in sorted_gl:
            if running_total + gl["amount"] <= bank["amount"] + tolerance:
                selected.append(gl)
                running_total += gl["amount"]
                if abs(running_total - bank["amount"]) <= tolerance:
                    break

        if len(selected) > 1 and abs(running_total - bank["amount"]) <= tolerance:
            return {
                "gl_txns": [g["original"] for g in selected],
                "gl_ids": [g["id"] for g in selected],
                "bank_txn": bank["original"],
                "bank_id": bank["id"],
                "match_type": MatchType.AGGREGATE.value,
                "confidence": 0.85,
                "gl_total": float(running_total),
                "bank_amount": float(bank["amount"]),
                "item_count": len(selected),
            }
        return None
