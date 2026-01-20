"""
Fuzzy Matching Engine for Financial Operations utility.

Matches customer/vendor names with confidence scoring:
- Handles LLC/Inc/Corp variations
- DBA name matching
- Levenshtein distance + token overlap
"""

import re
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .reconciliation import ReconciliationMixin

logger = get_logger(__name__)

# Common business suffixes to normalize
BUSINESS_SUFFIXES = [
    r"\bllc\b",
    r"\bl\.l\.c\.\b",
    r"\binc\b",
    r"\bincorporated\b",
    r"\bcorp\b",
    r"\bcorporation\b",
    r"\bco\b",
    r"\bcompany\b",
    r"\bltd\b",
    r"\blimited\b",
    r"\bplc\b",
    r"\blp\b",
    r"\bllp\b",
    r"\bpllc\b",
    r"\bpc\b",
    r"\bpa\b",
    r"\bna\b",
    r"\bd/b/a\b",
    r"\bdba\b",
]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row: list[int] = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row: list[int] = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate Levenshtein similarity (0-1) between two strings."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    distance = levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


def token_overlap_score(s1: str, s2: str) -> float:
    """Calculate token overlap score (Jaccard similarity on words)."""
    tokens1 = set(s1.lower().split())
    tokens2 = set(s2.lower().split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union)


class MatchingMixin(ReconciliationMixin):
    """Mixin providing fuzzy matching capabilities."""

    def fuzzy_match_entity(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Find best matching entity from candidates using fuzzy matching."""
        self._ensure_initialized()

        query, candidates, threshold, max_results = self._validate_match_args(args)
        query_normalized = self._normalize_entity_name(query)

        scored_matches = self._score_all_candidates(query_normalized, candidates, threshold)
        scored_matches.sort(key=lambda x: x["confidence"], reverse=True)

        result = self._build_match_result(
            query, query_normalized, candidates, scored_matches, max_results
        )

        logger.info(
            "Fuzzy match completed",
            service=self.SERVICE_NAME,
            query=query[:50],
            candidates_count=len(candidates),
            matches_found=len(scored_matches),
            best_confidence=scored_matches[0]["confidence"] if scored_matches else 0,
            log_event="fuzzy_match_complete",
        )
        self._track_usage()
        return result

    def _validate_match_args(
        self, args: dict[str, Any]
    ) -> tuple[str, list[dict[str, Any]], float, int]:
        """Validate and extract fuzzy match arguments."""
        query = args.get("query")
        if not query or not isinstance(query, str):
            raise ValidationError("query", "Query string required")

        candidates = args.get("candidates")
        if not candidates or not isinstance(candidates, list):
            raise ValidationError("candidates", "List of candidates required")

        threshold = float(args.get("threshold", 0.85))
        max_results = int(args.get("max_results", 5))
        return query, candidates, threshold, max_results

    def _score_all_candidates(
        self, query_normalized: str, candidates: list[dict[str, Any]], threshold: float
    ) -> list[dict[str, Any]]:
        """Score all candidates against normalized query."""
        scored_matches: list[dict[str, Any]] = []

        for candidate in candidates:
            candidate_id = candidate.get("id", "")
            candidate_name = candidate.get("name", "")
            aliases = candidate.get("aliases", [])

            best_score = self._score_match(query_normalized, candidate_name)
            matched_name = candidate_name

            for alias in aliases:
                alias_score = self._score_match(query_normalized, alias)
                if alias_score > best_score:
                    best_score = alias_score
                    matched_name = alias

            if best_score >= threshold:
                match_type = "exact" if best_score >= 0.99 else "fuzzy"
                scored_matches.append(
                    {
                        "id": candidate_id,
                        "name": candidate_name,
                        "matched_on": matched_name,
                        "confidence": round(best_score, 3),
                        "match_type": match_type,
                    }
                )

        return scored_matches

    def _build_match_result(
        self,
        query: str,
        query_normalized: str,
        candidates: list[dict[str, Any]],
        scored_matches: list[dict[str, Any]],
        max_results: int,
    ) -> dict[str, Any]:
        """Build the match result dictionary."""
        if not scored_matches:
            return {
                "best_match": None,
                "alternatives": [],
                "match_type": "no_match",
                "query": query,
                "query_normalized": query_normalized,
                "candidates_searched": len(candidates),
                "status": "success",
            }

        best = scored_matches[0]
        alternatives = scored_matches[1:max_results]
        return {
            "best_match": best,
            "alternatives": alternatives,
            "match_type": best["match_type"],
            "query": query,
            "query_normalized": query_normalized,
            "candidates_searched": len(candidates),
            "status": "success",
        }

    def _normalize_entity_name(self, name: str) -> str:
        """Normalize entity name for matching."""
        normalized = name.lower()
        for suffix in BUSINESS_SUFFIXES:
            normalized = re.sub(suffix, "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"[^\w\s']", " ", normalized)
        normalized = " ".join(normalized.split())
        return normalized.strip()

    def _score_match(self, query: str, candidate: str) -> float:
        """Calculate match score between query and candidate."""
        candidate_normalized = self._normalize_entity_name(candidate)

        if query == candidate_normalized:
            return 1.0

        lev_score = levenshtein_similarity(query, candidate_normalized)
        token_score = token_overlap_score(query, candidate_normalized)

        query_first = query.split()[0] if query.split() else ""
        candidate_first = candidate_normalized.split()[0] if candidate_normalized.split() else ""
        prefix_bonus = 0.1 if query_first == candidate_first else 0.0

        combined = (lev_score * 0.5) + (token_score * 0.4) + prefix_bonus
        return min(combined, 1.0)

    def match_transactions_by_entity(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Match transactions to entities using fuzzy name matching."""
        self._ensure_initialized()

        transactions = args.get("transactions")
        if not transactions or not isinstance(transactions, list):
            raise ValidationError("transactions", "List of transactions required")

        entities = args.get("entities")
        if not entities or not isinstance(entities, list):
            raise ValidationError("entities", "List of entities required")

        threshold = float(args.get("threshold", 0.85))

        matched, unmatched = self._match_transaction_list(
            org_id, user_id, transactions, entities, threshold
        )

        summary = {
            "total_transactions": len(transactions),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "match_rate": round(len(matched) / max(len(transactions), 1) * 100, 1),
        }

        logger.info(
            "Transaction entity matching completed",
            service=self.SERVICE_NAME,
            total=len(transactions),
            matched=len(matched),
            match_rate=summary["match_rate"],
            log_event="transaction_match_complete",
        )
        self._track_usage()

        return {
            "matched": matched,
            "unmatched": unmatched,
            "summary": summary,
            "status": "success",
        }

    def _match_transaction_list(
        self,
        org_id: str,
        user_id: str,
        transactions: list[dict[str, Any]],
        entities: list[dict[str, Any]],
        threshold: float,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Match a list of transactions against entities."""
        matched: list[dict[str, Any]] = []
        unmatched: list[dict[str, Any]] = []

        for txn in transactions:
            payer_name = txn.get("payer_name", "")
            if not payer_name:
                unmatched.append({**txn, "match_reason": "no_payer_name"})
                continue

            match_result = self.fuzzy_match_entity(
                org_id,
                user_id,
                {"query": payer_name, "candidates": entities, "threshold": threshold},
            )

            if match_result["best_match"]:
                matched.append(
                    {
                        **txn,
                        "matched_entity": match_result["best_match"],
                        "match_confidence": match_result["best_match"]["confidence"],
                    }
                )
            else:
                unmatched.append({**txn, "match_reason": "no_match_found"})

        return matched, unmatched
