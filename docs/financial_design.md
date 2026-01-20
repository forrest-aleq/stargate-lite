# Financial Analytics Design Specification

**Date:** 2025-10-25
**Phase:** 2 (Define Problems Properly)
**Component:** `src/shared/utilities/financial/analytics.py`
**Status:** Design - Architecture Corrected

---

## Architecture Layers

Following MARS 7-layer architecture (CLAUDE.md):

```
1. Primitives (src/shared/primitives/)
   └── VarianceAnalysisResult, ExpenseRecord, PropertyMetrics

2. Connectors (src/aleq_mind/connectors/)
   └── stargate_client.py (EXISTING) - talks to stargate-lite service

3. Utilities (src/shared/utilities/)
   └── financial/analytics.py (NEW) - VarianceAnalyzer, PeerComparison, ROICalculator

4. Nodes (src/aleq_mind/nodes/)
   └── insight_synthesis.py - calls utilities

5. Subgraphs (src/aleq_mind/subgraphs/)
   └── data_collection.py - caches aggregates monthly

6. Main Graph
   └── Routes to insight_synthesis node

7. Workflow
   └── User interaction
```

---

## Data Sourcing Architecture

### **Where Data Lives**

#### **Stargate-lite** (External Service)

- **Location:** Separate TypeScript repo (`/aleq/stargate-lite`)
- **Endpoint:** `POST /api/v1/execute` (capability-based API)
- **What it provides:** Raw financial data from QuickBooks/NetSuite
- **Available QuickBooks capabilities:**
  - `quickbooks.query_entities` - Query expenses, bills, invoices
  - `quickbooks.get_profit_loss_report` - P&L statement
  - `quickbooks.get_balance_sheet` - Balance sheet
  - `quickbooks.list_vendors` - Vendor list
  - `quickbooks.list_invoices` - Invoice list
  - `quickbooks.get_chart_of_accounts` - GL accounts

**Example stargate-lite usage:**

```python
# Via MARS connector (src/aleq_mind/connectors/stargate_client.py)
from aleq_mind.connectors.stargate_client import get_stargate_client

stargate = get_stargate_client()

response = stargate.execute_tool(
    tool_name="quickbooks.query_entities",
    args={
        "entity": "Expense",
        "query": "WHERE TxnDate >= '2024-01-01' AND TxnDate <= '2024-10-31'",
        "max_results": 1000
    },
    turn_id="turn_123",
    org_id="org_456",
    user_id="user_789"
)

if response.ok:
    expenses = response.result["entities"]  # List of expense objects
```

#### **Neo4j** (MARS Database)

- **What it provides:** CONTEXT not DATA
- **Knowledge nodes:** Learned variance thresholds, category mappings
- **Memory nodes:** Past variance events, outcomes, decisions
- **Entity nodes:** Property metadata (asset class, type, units), Equipment metadata (age, install date)
- **Metric nodes:** Cached monthly aggregates (NEW - to reduce stargate-lite calls)

**Example Neo4j usage:**

```cypher
// Fetch learned threshold for HVAC repairs
MATCH (org:Organization {org_id: $org_id})
MATCH (org)-[:HAS_KNOWLEDGE]->(k:Knowledge)
WHERE k.knowledge_type = 'variance_threshold'
  AND k.category = 'HVAC Repairs'
RETURN k.threshold_percent, k.confidence
```

#### **Synthesis = Competitive Advantage**

```python
# Step 1: Fetch raw data from stargate-lite (fresh)
expenses = stargate.execute_tool("quickbooks.query_entities", ...)

# Step 2: Fetch context from Neo4j (learned thresholds, equipment age)
context = neo4j.execute_query("""
    MATCH (prop:Property)-[:HAS_EQUIPMENT]->(equip:Equipment)
    MATCH (org)-[:HAS_KNOWLEDGE]->(k:Knowledge)
    RETURN equip.age, k.threshold_percent
""")

# Step 3: Synthesize variance analysis
variance = VarianceAnalyzer.analyze_variance(
    actual=sum([e["amount"] for e in expenses]),  # From stargate-lite
    budget=budget,  # From stargate-lite or Neo4j
    threshold=context["threshold_percent"],  # From Neo4j
    equipment_age=context["age"]  # From Neo4j
)
```

---

## Strategic Positioning: What Aleq Does That ChatGPT/Claude/Gemini Can't

### What General-Purpose LLMs CAN Do:

- ✅ Analyze pasted financial data
- ✅ Explain variances when asked
- ✅ Statistical analysis comparable to Stata
- ✅ Pattern detection in provided data

### What They CANNOT Do:

- ❌ **Persistent memory** - Stateless APIs
- ❌ **Multi-source integration** - Can't auto-pull QB + Neo4j
- ❌ **Proactive monitoring** - Won't detect "3rd HVAC failure in 90 days" unless asked
- ❌ **Entity relationships** - No knowledge graph of YOUR business
- ❌ **Temporal intelligence** - Can't track "this is getting worse over time"
- ❌ **Personalized thresholds** - Use generic 10%, not context-aware 15%
- ❌ **Action integration** - Can't trigger vendor review workflows
- ❌ **Authority-aware insights** - Don't know which insights you trust

**Aleq's advantage:**

1. Continuous observation (proactive)
2. Context-aware (YOUR properties, YOUR vendors, YOUR history)
3. Actionable workflows (analytics trigger subgraphs)
4. Learning system (builds Beliefs, updates thresholds)
5. Multi-source synthesis (QB + Neo4j Memory + peer data)

---

## Component 1: VarianceAnalyzer

**File:** `src/shared/utilities/financial/analytics.py`
**Layer:** Utilities (layer 3)

### Input Schema (Primitives)

```python
# src/shared/primitives/financial.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class PropertyContext:
    """Property metadata for context-aware analysis"""
    property_id: str
    asset_class: str  # "A", "B", "C"
    property_type: str  # "garden", "mid-rise", "high-rise"
    unit_count: int
    square_footage: int
    vintage_year: int
    msa: str  # Metropolitan Statistical Area
    occupancy_rate: float

@dataclass
class ExpenseRecord:
    """Individual expense from QuickBooks via stargate-lite"""
    transaction_id: str
    date: datetime
    category: str
    vendor_name: str
    amount: float
    property_id: str
    description: Optional[str] = None

@dataclass
class HistoricalData:
    """Historical expenses for trend analysis"""
    category: str
    property_id: str
    monthly_amounts: List[float]  # Last 12-24 months
    dates: List[datetime]
```

### Output Schema (Primitives)

```python
@dataclass
class VarianceAnalysis:
    """Rich variance analysis output"""

    # Basic variance
    actual: float
    budget: float
    variance_amount: float
    variance_percent: float

    # Context-aware severity
    severity: str  # "low", "medium", "high", "critical"
    severity_score: float  # 0.0-1.0

    # Seasonally-adjusted variance
    seasonal_adjusted_variance: float
    seasonal_factor: Optional[float]

    # Trend analysis
    trend_direction: str  # "improving", "stable", "deteriorating"
    trend_slope: Optional[float]
    trend_confidence: float  # R² value

    # Peer comparison
    peer_percentile: Optional[float]  # 0-100
    peer_median: Optional[float]
    peer_iqr: Optional[tuple[float, float]]
    cohort_size: int

    # Root cause hypothesis
    root_cause_type: str  # "price", "volume", "equipment_failure", "event", "unknown"
    root_cause_evidence: List[str]
    linked_entities: List[str]  # Entity IDs from Neo4j

    # Confidence
    confidence_score: float  # 0.0-1.0
    data_quality_notes: List[str]
```

### Core Algorithm (Utility)

```python
# src/shared/utilities/financial/analytics.py
import logging
from typing import Dict, List, Optional
from statsmodels.tsa.seasonal import seasonal_decompose
from scipy.stats import linregress
import numpy as np
import pandas as pd

from shared.primitives.financial import (
    PropertyContext, ExpenseRecord, HistoricalData, VarianceAnalysis
)
from aleq_mind.connectors.stargate_client import StargateClient
from shared.connectors.neo4j_connection import Neo4jConnection

logger = logging.getLogger(__name__)


class VarianceAnalyzer:
    """
    Context-aware variance analysis using stargate-lite + Neo4j

    Data flow:
    1. Fetch raw expenses from QuickBooks via stargate-lite
    2. Fetch context (thresholds, equipment, memories) from Neo4j
    3. Perform statistical analysis (seasonal adjustment, trends)
    4. Calculate peer comparison
    5. Hypothesize root cause
    6. Return VarianceAnalysis
    """

    def __init__(
        self,
        stargate: StargateClient,
        neo4j: Neo4jConnection
    ):
        self.stargate = stargate
        self.neo4j = neo4j

    async def analyze_variance(
        self,
        category: str,
        property_context: PropertyContext,
        month: str,  # e.g., "2024-10"
        org_id: str,
        user_id: str,
        turn_id: str
    ) -> VarianceAnalysis:
        """
        Perform context-aware variance analysis

        Steps:
        1. Fetch actual expenses from QuickBooks (via stargate-lite)
        2. Fetch budget from QuickBooks or Neo4j
        3. Fetch learned threshold from Neo4j
        4. Fetch historical data (cached aggregates or fresh from QB)
        5. Perform seasonal adjustment
        6. Calculate trend
        7. Fetch peer cohort and calculate percentile
        8. Hypothesize root cause (combine stargate + neo4j data)
        9. Calculate severity and confidence
        """

        # Step 1: Fetch actual expenses from QuickBooks
        actual = await self._fetch_actual_expenses(
            category=category,
            property_id=property_context.property_id,
            month=month,
            org_id=org_id,
            user_id=user_id,
            turn_id=turn_id
        )

        # Step 2: Fetch budget
        budget = await self._fetch_budget(
            category=category,
            property_id=property_context.property_id,
            month=month,
            org_id=org_id,
            user_id=user_id,
            turn_id=turn_id
        )

        # Basic variance
        variance_amount = actual - budget
        variance_percent = (variance_amount / budget) if budget != 0 else 0.0

        # Step 3: Fetch learned threshold from Neo4j
        threshold = await self._get_context_threshold(
            category=category,
            property_type=property_context.property_type,
            asset_class=property_context.asset_class,
            org_id=org_id
        )

        # Step 4: Fetch historical data
        historical_data = await self._fetch_historical_data(
            category=category,
            property_id=property_context.property_id,
            org_id=org_id,
            user_id=user_id,
            turn_id=turn_id
        )

        # Step 5: Seasonal adjustment
        seasonal_adjusted, seasonal_factor = self._seasonal_adjust(
            historical_data.monthly_amounts,
            historical_data.dates
        )

        # Step 6: Trend analysis
        trend_direction, trend_slope, trend_confidence = self._calculate_trend(
            historical_data.monthly_amounts,
            historical_data.dates
        )

        # Step 7: Peer comparison
        peer_data = await self._fetch_peer_cohort(
            category=category,
            property_context=property_context,
            month=month,
            org_id=org_id,
            user_id=user_id,
            turn_id=turn_id
        )

        peer_percentile, peer_median, peer_iqr = self._calculate_peer_metrics(
            actual=actual,
            peer_amounts=peer_data
        )

        # Step 8: Root cause hypothesis
        root_cause_type, root_cause_evidence, linked_entities = await self._hypothesize_root_cause(
            category=category,
            property_id=property_context.property_id,
            variance_amount=variance_amount,
            month=month,
            org_id=org_id,
            user_id=user_id,
            turn_id=turn_id
        )

        # Step 9: Severity and confidence
        severity, severity_score = self._calculate_severity(
            variance_percent=variance_percent,
            threshold=threshold,
            trend_direction=trend_direction,
            peer_percentile=peer_percentile
        )

        confidence_score, data_quality_notes = self._calculate_confidence(
            historical_data=historical_data,
            peer_cohort_size=len(peer_data),
            seasonal_factor=seasonal_factor
        )

        return VarianceAnalysis(
            actual=actual,
            budget=budget,
            variance_amount=variance_amount,
            variance_percent=variance_percent,
            severity=severity,
            severity_score=severity_score,
            seasonal_adjusted_variance=seasonal_adjusted,
            seasonal_factor=seasonal_factor,
            trend_direction=trend_direction,
            trend_slope=trend_slope,
            trend_confidence=trend_confidence,
            peer_percentile=peer_percentile,
            peer_median=peer_median,
            peer_iqr=peer_iqr,
            cohort_size=len(peer_data),
            root_cause_type=root_cause_type,
            root_cause_evidence=root_cause_evidence,
            linked_entities=linked_entities,
            confidence_score=confidence_score,
            data_quality_notes=data_quality_notes
        )

    # =========================================================================
    # Stargate Integration (Connector Layer)
    # =========================================================================

    async def _fetch_actual_expenses(
        self,
        category: str,
        property_id: str,
        month: str,  # "2024-10"
        org_id: str,
        user_id: str,
        turn_id: str
    ) -> float:
        """
        Fetch actual expenses from QuickBooks via stargate-lite

        Uses quickbooks.query_entities capability
        """
        # Parse month to date range
        year, month_num = month.split("-")
        start_date = f"{year}-{month_num}-01"

        # Calculate end date (last day of month)
        if month_num == "12":
            end_date = f"{year}-12-31"
        else:
            next_month = int(month_num) + 1
            end_date = f"{year}-{next_month:02d}-01"

        try:
            response = await self.stargate.execute_tool(
                tool_name="quickbooks.query_entities",
                args={
                    "entity": "Expense",
                    "query": f"WHERE TxnDate >= '{start_date}' AND TxnDate < '{end_date}'",
                    "max_results": 1000
                },
                turn_id=turn_id,
                org_id=org_id,
                user_id=user_id
            )

            if not response.ok:
                logger.error(f"Failed to fetch expenses from QB: {response.result}")
                return 0.0

            expenses = response.result.get("entities", [])

            # Filter by property_id and category
            filtered_expenses = [
                e for e in expenses
                if e.get("property_id") == property_id
                and e.get("category") == category
            ]

            total = sum([e.get("amount", 0.0) for e in filtered_expenses])

            logger.info(
                f"Fetched {len(filtered_expenses)} expenses for {property_id}/{category} "
                f"in {month}: ${total:,.2f}"
            )

            return total

        except Exception as e:
            logger.error(f"Error fetching expenses from QB: {e}")
            return 0.0

    async def _fetch_budget(
        self,
        category: str,
        property_id: str,
        month: str,
        org_id: str,
        user_id: str,
        turn_id: str
    ) -> float:
        """
        Fetch budget from QuickBooks or Neo4j Knowledge

        Try stargate-lite first, fallback to Neo4j if not available
        """
        # TODO: Implement QB budget fetch if available
        # For now, fallback to Neo4j Knowledge

        query = """
        MATCH (prop:Property {property_id: $property_id})
        MATCH (prop)-[:HAS_KNOWLEDGE]->(k:Knowledge)
        WHERE k.knowledge_type = 'budget'
          AND k.category = $category
          AND k.month = $month
        RETURN k.amount as budget
        """

        result = await self.neo4j.execute_query(
            query,
            property_id=property_id,
            category=category,
            month=month
        )

        if result and len(result) > 0:
            return result[0].get("budget", 0.0)

        logger.warning(
            f"No budget found for {property_id}/{category}/{month}, using 0.0"
        )
        return 0.0

    async def _fetch_historical_data(
        self,
        category: str,
        property_id: str,
        org_id: str,
        user_id: str,
        turn_id: str,
        lookback_months: int = 12
    ) -> HistoricalData:
        """
        Fetch historical expense data

        Strategy:
        1. Check Neo4j for cached :Metric nodes (fast)
        2. If missing, fetch from QuickBooks via stargate-lite (slow)
        """
        # Try cached metrics first
        query = """
        MATCH (prop:Property {property_id: $property_id})
        MATCH (prop)-[:HAS_METRIC]->(m:Metric)
        WHERE m.category = $category
          AND m.metric_type = 'expense_total'
        RETURN m.month, m.total_amount
        ORDER BY m.month DESC
        LIMIT $lookback_months
        """

        cached_results = await self.neo4j.execute_query(
            query,
            property_id=property_id,
            category=category,
            lookback_months=lookback_months
        )

        if cached_results and len(cached_results) >= 6:
            # Have enough cached data
            monthly_amounts = [r["total_amount"] for r in reversed(cached_results)]
            dates = [
                pd.to_datetime(r["month"] + "-01")
                for r in reversed(cached_results)
            ]

            return HistoricalData(
                category=category,
                property_id=property_id,
                monthly_amounts=monthly_amounts,
                dates=dates
            )

        # Fallback: Fetch from QuickBooks (expensive)
        logger.warning(
            f"Insufficient cached data for {property_id}/{category}, "
            f"fetching from QuickBooks"
        )

        # TODO: Implement QB historical fetch
        # For now, return empty
        return HistoricalData(
            category=category,
            property_id=property_id,
            monthly_amounts=[],
            dates=[]
        )

    # =========================================================================
    # Neo4j Integration
    # =========================================================================

    async def _get_context_threshold(
        self,
        category: str,
        property_type: str,
        asset_class: str,
        org_id: str
    ) -> Dict[str, float]:
        """Fetch learned variance threshold from Neo4j"""

        query = """
        MATCH (org:Organization {org_id: $org_id})
        OPTIONAL MATCH (org)-[:HAS_KNOWLEDGE]->(k1:Knowledge)
        WHERE k1.knowledge_type = 'variance_threshold'
          AND k1.category = $category
          AND k1.property_type = $property_type
          AND k1.asset_class = $asset_class
        OPTIONAL MATCH (org)-[:HAS_KNOWLEDGE]->(k2:Knowledge)
        WHERE k2.knowledge_type = 'variance_threshold'
          AND k2.category = $category
          AND k2.property_type IS NULL
        OPTIONAL MATCH (org)-[:HAS_KNOWLEDGE]->(k3:Knowledge)
        WHERE k3.knowledge_type = 'variance_threshold'
          AND k3.category = 'default'
        WITH COALESCE(k1, k2, k3) as threshold_knowledge
        RETURN
          threshold_knowledge.threshold_percent as threshold_percent,
          threshold_knowledge.confidence as confidence
        """

        result = await self.neo4j.execute_query(
            query,
            org_id=org_id,
            category=category,
            property_type=property_type,
            asset_class=asset_class
        )

        if result and len(result) > 0:
            return {
                'threshold_percent': result[0]['threshold_percent'],
                'confidence': result[0]['confidence']
            }
        else:
            # Fallback to hardcoded default
            return {
                'threshold_percent': 0.10,  # Generic 10%
                'confidence': 0.5
            }

    # =========================================================================
    # Statistical Methods (Pure utility functions)
    # =========================================================================

    def _seasonal_adjust(
        self,
        monthly_amounts: List[float],
        dates: List[datetime]
    ) -> tuple[float, Optional[float]]:
        """Seasonal decomposition using statsmodels"""
        if len(monthly_amounts) < 24:
            return (monthly_amounts[-1] if monthly_amounts else 0.0, None)

        try:
            series = pd.Series(monthly_amounts, index=pd.DatetimeIndex(dates))
            decomposition = seasonal_decompose(series, model='additive', period=12)
            seasonal_factor = decomposition.seasonal.iloc[-1]
            observed = monthly_amounts[-1]
            seasonally_adjusted = observed - seasonal_factor
            return (seasonally_adjusted, seasonal_factor)
        except Exception as e:
            logger.warning(f"Seasonal adjustment failed: {e}")
            return (monthly_amounts[-1] if monthly_amounts else 0.0, None)

    def _calculate_trend(
        self,
        monthly_amounts: List[float],
        dates: List[datetime]
    ) -> tuple[str, Optional[float], float]:
        """Linear regression trend analysis"""
        if len(monthly_amounts) < 6:
            return ("unknown", None, 0.0)

        x = np.arange(len(monthly_amounts))
        y = np.array(monthly_amounts)
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        r_squared = r_value ** 2

        if p_value > 0.05:
            trend_direction = "stable"
        elif slope > np.mean(y) * 0.02:
            trend_direction = "deteriorating"
        elif slope < -np.mean(y) * 0.02:
            trend_direction = "improving"
        else:
            trend_direction = "stable"

        return (trend_direction, slope, r_squared)

    def _calculate_peer_metrics(
        self,
        actual: float,
        peer_amounts: List[float]
    ) -> tuple[Optional[float], Optional[float], Optional[tuple[float, float]]]:
        """Calculate percentile and IQR"""
        if not peer_amounts or len(peer_amounts) < 3:
            return (None, None, None)

        peer_array = np.array(peer_amounts)
        percentile = (np.sum(peer_array < actual) / len(peer_array)) * 100
        median = np.median(peer_array)
        q25 = np.percentile(peer_array, 25)
        q75 = np.percentile(peer_array, 75)
        iqr = (q25, q75)

        return (percentile, median, iqr)

    def _calculate_severity(
        self,
        variance_percent: float,
        threshold: Dict[str, float],
        trend_direction: str,
        peer_percentile: Optional[float]
    ) -> tuple[str, float]:
        """Multi-factor severity scoring"""
        score = 0.0
        threshold_pct = threshold['threshold_percent']

        # Factor 1: Magnitude (40%)
        if abs(variance_percent) >= threshold_pct * 2:
            score += 0.4
        elif abs(variance_percent) >= threshold_pct:
            score += 0.25
        elif abs(variance_percent) >= threshold_pct * 0.5:
            score += 0.10

        # Factor 2: Trend (30%)
        if trend_direction == "deteriorating":
            score += 0.3
        elif trend_direction == "stable":
            score += 0.1

        # Factor 3: Peer comparison (30%)
        if peer_percentile is not None:
            if peer_percentile >= 90:
                score += 0.3
            elif peer_percentile >= 75:
                score += 0.2
            elif peer_percentile >= 50:
                score += 0.1

        # Severity label
        if score >= 0.7:
            severity = "critical"
        elif score >= 0.5:
            severity = "high"
        elif score >= 0.3:
            severity = "medium"
        else:
            severity = "low"

        return (severity, score)

    def _calculate_confidence(
        self,
        historical_data: HistoricalData,
        peer_cohort_size: int,
        seasonal_factor: Optional[float]
    ) -> tuple[float, List[str]]:
        """Data quality-based confidence scoring"""
        confidence = 1.0
        notes = []

        # Historical data quality
        if len(historical_data.monthly_amounts) < 6:
            confidence -= 0.3
            notes.append("Limited historical data (< 6 months)")
        elif len(historical_data.monthly_amounts) < 12:
            confidence -= 0.1
            notes.append("Moderate historical data (6-11 months)")

        # Peer cohort size
        if peer_cohort_size < 3:
            confidence -= 0.3
            notes.append(f"Small peer cohort (n={peer_cohort_size})")
        elif peer_cohort_size < 5:
            confidence -= 0.1
            notes.append(f"Limited peer cohort (n={peer_cohort_size})")

        # Seasonal adjustment
        if seasonal_factor is None and len(historical_data.monthly_amounts) >= 12:
            confidence -= 0.1
            notes.append("Seasonal adjustment failed")

        return (max(confidence, 0.0), notes)

    async def _fetch_peer_cohort(
        self,
        category: str,
        property_context: PropertyContext,
        month: str,
        org_id: str,
        user_id: str,
        turn_id: str
    ) -> List[float]:
        """
        Fetch peer cohort expense totals

        Two-phase:
        1. Identify peer properties from Neo4j (metadata matching)
        2. Fetch cached expense totals from Neo4j :Metric nodes
           (or from QuickBooks if not cached)
        """
        # Phase 1: Identify peers
        peer_query = """
        MATCH (org:Organization {org_id: $org_id})
        MATCH (org)-[:OWNS]->(peer:Property)
        WHERE peer.property_type = $property_type
          AND peer.asset_class = $asset_class
          AND peer.unit_count >= $min_units
          AND peer.unit_count <= $max_units
          AND peer.msa = $msa
          AND peer.property_id <> $property_id
        RETURN peer.property_id as property_id
        """

        peer_results = await self.neo4j.execute_query(
            peer_query,
            org_id=org_id,
            property_type=property_context.property_type,
            asset_class=property_context.asset_class,
            min_units=int(property_context.unit_count * 0.7),
            max_units=int(property_context.unit_count * 1.3),
            msa=property_context.msa,
            property_id=property_context.property_id
        )

        peer_property_ids = [r['property_id'] for r in peer_results]

        if len(peer_property_ids) < 3:
            logger.warning(
                f"Too few peers found ({len(peer_property_ids)}), "
                f"peer comparison will have low confidence"
            )

        # Phase 2: Fetch cached expense totals
        cached_query = """
        MATCH (peer:Property)
        WHERE peer.property_id IN $peer_property_ids
        MATCH (peer)-[:HAS_METRIC]->(metric:Metric)
        WHERE metric.category = $category
          AND metric.month = $month
          AND metric.metric_type = 'expense_total'
        RETURN peer.property_id, metric.total_amount
        """

        cached_results = await self.neo4j.execute_query(
            cached_query,
            peer_property_ids=peer_property_ids,
            category=category,
            month=month
        )

        peer_amounts = [r['total_amount'] for r in cached_results]

        # If missing cached data for some peers, could fetch from QB
        # but that's expensive - skip for now

        return peer_amounts

    async def _hypothesize_root_cause(
        self,
        category: str,
        property_id: str,
        variance_amount: float,
        month: str,
        org_id: str,
        user_id: str,
        turn_id: str
    ) -> tuple[str, List[str], List[str]]:
        """
        Root cause hypothesis using stargate + Neo4j

        Phase 1: Fetch transaction details from QuickBooks
        Phase 2: Fetch entity context from Neo4j
        Phase 3: Synthesize hypothesis
        """
        # Phase 1: Transaction analysis from QB
        try:
            year, month_num = month.split("-")
            start_date = f"{year}-{month_num}-01"

            response = await self.stargate.execute_tool(
                tool_name="quickbooks.query_entities",
                args={
                    "entity": "Expense",
                    "query": f"WHERE TxnDate >= '{start_date}' AND property_id = '{property_id}' AND category = '{category}'",
                    "max_results": 100
                },
                turn_id=turn_id,
                org_id=org_id,
                user_id=user_id
            )

            if not response.ok:
                return ("unknown", ["Failed to fetch transaction data"], [])

            transactions = response.result.get("entities", [])
            unique_vendors = set([t.get("vendor_id") for t in transactions if t.get("vendor_id")])
            transaction_count = len(transactions)

        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            return ("unknown", ["Transaction data unavailable"], [])

        # Phase 2: Entity context from Neo4j
        equipment_type = self._infer_equipment_type(category)

        neo4j_query = """
        MATCH (prop:Property {property_id: $property_id})
        OPTIONAL MATCH (prop)-[:HAS_EQUIPMENT]->(equip:Equipment)
        WHERE equip.equipment_type = $equipment_type
        OPTIONAL MATCH (prop)-[:HAS_MEMORY]->(mem:Memory)
        WHERE mem.memory_type IN ['equipment_failure', 'variance_event']
          AND mem.category = $category
        RETURN
          COLLECT(DISTINCT {
            equipment_id: equip.equipment_id,
            age: equip.age,
            failure_count: SIZE((equip)<-[:RELATED_TO]-(:Memory {memory_type: 'equipment_failure'}))
          }) as equipment_context,
          COUNT(DISTINCT mem) as failure_memory_count
        """

        neo4j_results = await self.neo4j.execute_query(
            neo4j_query,
            property_id=property_id,
            equipment_type=equipment_type,
            category=category
        )

        equipment_context = neo4j_results[0]['equipment_context'] if neo4j_results else []

        # Phase 3: Synthesize
        # Equipment failure pattern
        if transaction_count >= 3 and equipment_context:
            for equip in equipment_context:
                if equip['failure_count'] >= 2:
                    return (
                        "equipment_failure",
                        [
                            f"{transaction_count} repair transactions",
                            f"Equipment {equip['equipment_id']} has {equip['failure_count']} prior failures",
                            f"Equipment age: {equip['age']} years"
                        ],
                        [equip['equipment_id']]
                    )

        # Vendor switching pattern
        if len(unique_vendors) >= 2:
            return (
                "vendor_switching",
                [
                    f"Used {len(unique_vendors)} different vendors",
                    f"{transaction_count} total transactions",
                    "Possible price shopping or vendor issues"
                ],
                list(unique_vendors)
            )

        # Volume increase
        if transaction_count > 5:
            return (
                "volume_increase",
                [f"{transaction_count} transactions (frequency increase)"],
                []
            )

        return ("unknown", ["Pattern unclear"], [])

    def _infer_equipment_type(self, category: str) -> str:
        """Map expense category to equipment type"""
        mapping = {
            "HVAC Repairs": "HVAC",
            "Plumbing": "Plumbing",
            "Electrical": "Electrical",
            "Appliance Repairs": "Appliance",
            "Landscaping": "Landscaping"
        }
        return mapping.get(category, "General")
```

---

## Integration with Nodes

### Insight Synthesis Node

**File:** `src/aleq_mind/nodes/insight_synthesis.py`

```python
from aleq_mind.connectors.stargate_client import get_stargate_client
from shared.connectors.neo4j_connection import get_neo4j_connection
from shared.utilities.financial.analytics import VarianceAnalyzer
from shared.primitives.financial import PropertyContext

async def insight_synthesis_node(state: dict) -> dict:
    """
    Node that generates financial insights

    Called when user asks: "What should I watch with expenses?"
    """
    stargate = get_stargate_client()
    neo4j = get_neo4j_connection()

    analyzer = VarianceAnalyzer(stargate=stargate, neo4j=neo4j)

    # Fetch user's properties
    properties = await fetch_user_properties(state["org_id"])

    # Analyze variances for major categories
    categories = ["HVAC Repairs", "Plumbing", "Landscaping", "Legal Fees"]
    insights = []

    for prop in properties:
        property_context = PropertyContext(
            property_id=prop["property_id"],
            asset_class=prop["asset_class"],
            property_type=prop["property_type"],
            unit_count=prop["unit_count"],
            square_footage=prop["square_footage"],
            vintage_year=prop["vintage_year"],
            msa=prop["msa"],
            occupancy_rate=prop["occupancy_rate"]
        )

        for category in categories:
            variance = await analyzer.analyze_variance(
                category=category,
                property_context=property_context,
                month="2024-10",
                org_id=state["org_id"],
                user_id=state["user_id"],
                turn_id=state["turn_id"]
            )

            if variance.severity in ["high", "critical"]:
                insights.append(variance)

    # Sort by severity and return top 5
    insights.sort(key=lambda v: v.severity_score, reverse=True)
    top_insights = insights[:5]

    # Generate natural language response
    response = format_insights_response(top_insights)

    return {"response": response, "insights": top_insights}
```

---

## Data Collection Subgraph

**File:** `src/aleq_mind/subgraphs/data_collection.py`

Runs monthly to cache expense aggregates in Neo4j `:Metric` nodes.

```python
async def cache_monthly_metrics_node(state: dict) -> dict:
    """
    Node that caches monthly expense aggregates from QuickBooks to Neo4j

    Runs: 1st of each month at 2am
    Purpose: Reduce repeated stargate-lite calls
    """
    stargate = get_stargate_client()
    neo4j = get_neo4j_connection()

    # Get all properties for org
    properties = await fetch_all_properties(state["org_id"])
    categories = ["HVAC Repairs", "Plumbing", "Electrical", "Landscaping", "Legal Fees"]

    previous_month = get_previous_month()  # e.g., "2024-09"

    for prop in properties:
        for category in categories:
            # Fetch from QuickBooks
            analyzer = VarianceAnalyzer(stargate=stargate, neo4j=neo4j)
            total = await analyzer._fetch_actual_expenses(
                category=category,
                property_id=prop["property_id"],
                month=previous_month,
                org_id=state["org_id"],
                user_id=state["user_id"],
                turn_id=state["turn_id"]
            )

            # Cache in Neo4j
            await neo4j.execute_query("""
                MATCH (prop:Property {property_id: $property_id})
                MERGE (prop)-[:HAS_METRIC]->(m:Metric {
                    property_id: $property_id,
                    category: $category,
                    month: $month
                })
                SET m.metric_type = 'expense_total',
                    m.total_amount = $total,
                    m.last_updated = datetime()
            """, property_id=prop["property_id"], category=category, month=previous_month, total=total)

    return state
```

---

## Neo4j Schema

### Metric Nodes (Cached Aggregates)

```cypher
CREATE (m:Metric {
  metric_id: "metric_oak_hvac_2024_10",
  org_id: "org_12345",
  property_id: "prop_oak_street",
  metric_type: "expense_total",
  category: "HVAC Repairs",
  month: "2024-10",
  total_amount: 12847.50,
  transaction_count: 3,
  last_updated: datetime()
})

MATCH (prop:Property {property_id: "prop_oak_street"})
CREATE (prop)-[:HAS_METRIC]->(m)
```

### Knowledge Nodes (Thresholds)

```cypher
CREATE (k:Knowledge {
  knowledge_id: "kt_hvac_garden_a_12345",
  org_id: "org_12345",
  knowledge_type: "variance_threshold",
  category: "HVAC Repairs",
  property_type: "garden",
  asset_class: "A",
  threshold_percent: 0.15,  // 15% not 10%
  confidence: 0.92,
  sample_size: 47,
  last_updated: datetime()
})
```

### Equipment Nodes (Context)

```cypher
CREATE (e:Equipment {
  equipment_id: "equip_hvac_oak_unit_3",
  org_id: "org_12345",
  property_id: "prop_oak_street",
  equipment_type: "HVAC",
  manufacturer: "Carrier",
  install_date: date("2005-03-15"),
  age: 19
})

MATCH (prop:Property {property_id: "prop_oak_street"})
CREATE (prop)-[:HAS_EQUIPMENT]->(e)
```

---

## Dependencies

### Python Libraries

```bash
pip install statsmodels scipy numpy pandas httpx
```

### Stargate-lite Service (CRITICAL)

- **Location:** Separate repo `/aleq/stargate-lite`
- **Endpoint:** `http://localhost:8001` (or configured via `STARGATE_BASE_URL`)
- **API Key:** Required in `STARGATE_API_KEY` env var
- **Required capabilities:**
  - `quickbooks.query_entities` - Query expenses
  - `quickbooks.get_profit_loss_report` - P&L (optional)
  - `quickbooks.list_vendors` - Vendor metadata (for root cause)

### MARS Connector (EXISTS)

- **File:** `src/aleq_mind/connectors/stargate_client.py`
- **Usage:** `get_stargate_client()` dependency injection
- **Already implemented:** HTTP client, idempotency, error handling

---

## Open Questions

1. **QuickBooks query syntax:** What is the exact query syntax for `quickbooks.query_entities`? Need stargate-lite docs or examples.
2. **Property ID in QuickBooks:** Do QB expense records have a `property_id` field? Or do we need to map via GL account/class/location?
3. **Metric caching schedule:** Should Data Collection Subgraph run monthly (1st at 2am) or more frequently?
4. **Budget source:** Where do budgets live? QuickBooks? NetSuite? Or should we store in Neo4j Knowledge?
5. **Threshold learning:** How do we update variance thresholds based on outcomes? Weekly batch job analyzing Memory outcomes?
6. **Peer cohort caching:** Should we cache peer property IDs in Redis (7-day TTL)?
7. **Multi-property aggregation:** Analyze 50 properties individually or aggregate by asset class first?
8. **Confidence threshold:** At what confidence score do we suppress insights? (Proposed: < 0.5)

---

## Stargate-Lite Clarifications & Answers

**Date:** 2025-10-25
**Source:** `/Users/forrest/Documents/Projects/aleq/stargate-lite`

### Architecture Correction

**INCORRECT:** "Separate TypeScript repo--youre likely refergint to conversational-workflow-builder"
**CORRECT:** Python/FastAPI service located at `/Users/forrest/Documents/Projects/aleq/stargate-lite`

- **Framework:** FastAPI + Uvicorn
- **Runtime:** Python 3.13
- **Database:** SQLAlchemy (SQLite dev / PostgreSQL prod)
- **Encryption:** Fernet symmetric encryption for OAuth tokens

---

### API Endpoint Structure

#### Request Format

```python
POST http://localhost:8001/api/v1/execute
Headers:
  X-API-Key: <API_SECRET_KEY>
  Content-Type: application/json

Body:
{
  "capability_key": "qb.query",           # Abstract capability (registry key)
  "org_id": "org_12345",                   # Multi-tenant organization ID
  "user_id": "user_67890",                 # User for credential lookup
  "args": {                                # Tool-specific arguments
    "query": "SELECT * FROM Expense WHERE TxnDate >= '2024-10-01'"
  }
}
```

#### Response Format

```python
{
  "ok": true,
  "result": {
    "results": {
      "Expense": [
        {
          "Id": "123",
          "Amount": 1250.00,
          "TxnDate": "2024-10-15",
          "AccountRef": {"value": "67", "name": "Repairs & Maintenance"},
          "EntityRef": {"value": "45", "name": "Acme Plumbing"},
          "PrivateNote": "Unit 3B emergency repair",
          "ClassRef": {"value": "10", "name": "Oak Street Apartments"}
        }
      ]
    },
    "count": 1
  },
  "logs": ["Resolved capability 'qb.query' to tool 'quickbooks.query_entities'"]
}
```

---

### Capability Key Naming (Registry Mappings)

**IMPORTANT:** Capability keys are **NOT** prefixed with service names. The registry abstracts service implementation.

#### Financial Analytics Capabilities (QuickBooks)

| Capability Key               | Handler                                 | Description                                 | October 2025 API |
| ---------------------------- | --------------------------------------- | ------------------------------------------- | ---------------- |
| `qb.query`                 | `qb_connector.query_entities`         | SQL-like query (SELECT * FROM Entity)       | ✅               |
| `report.profitloss`        | `qb_connector.get_profit_loss_report` | Summary P&L report                          | ✅               |
| `report.profitloss.detail` | `qb_connector.get_profit_loss_detail` | **Detailed P&L with transactions**    | ✅ NEW           |
| `budget.get`               | `qb_connector.get_budget`             | **Budget data for variance analysis** | ✅ NEW           |
| `chartofaccounts.get`      | `qb_connector.get_chart_of_accounts`  | GL account list                             | ✅               |
| `vendor.list`              | `qb_connector.list_vendors`           | Vendor metadata                             | ✅               |
| `vendor.get`               | `qb_connector.get_vendor`             | Single vendor by ID                         | ✅               |
| `vendor.create`            | `qb_connector.create_vendor`          | Create new vendor                           | ✅               |
| `expense.create`           | `qb_connector.create_expense`         | Create expense transaction                  | ✅               |
| `document.upload`          | `qb_connector.upload_attachment`      | **Upload W-9/invoice/receipt**        | ✅ NEW           |

**Total QB capabilities:** 279 across all platforms (288 with Hyperbrowser)

---

### Query Syntax (Answer to Question 1)

**Capability:** `qb.query`
**Syntax:** QuickBooks SQL-like query language (not true SQL)

#### Supported Entities

```
Vendor, Customer, Expense, Bill, Invoice, Payment,
Account, Class, Department, Item, JournalEntry
```

#### Query Examples

**Fetch October 2024 expenses:**

```python
await stargate.execute_tool(
    capability_key="qb.query",
    args={
        "query": "SELECT * FROM Expense WHERE TxnDate >= '2024-10-01' AND TxnDate <= '2024-10-31'"
    },
    org_id=org_id,
    user_id=user_id
)
```

**Fetch expenses for specific account:**

```python
args={
    "query": "SELECT * FROM Expense WHERE AccountRef = '67'"  # Account ID
}
```

**Fetch bills from specific vendor:**

```python
args={
    "query": "SELECT * FROM Bill WHERE VendorRef = '45' AND TxnDate >= '2024-01-01'"
}
```

#### Limitations

- No JOINs (single entity per query)
- No aggregations (SUM/COUNT/AVG - must aggregate client-side)
- Limited WHERE clause operators: `=`, `>`, `<`, `>=`, `<=`, `IN`
- Max results: 1000 per query (pagination required for larger sets)

---

### Property ID Mapping (Answer to Question 2)

**CRITICAL:** QuickBooks does **NOT** have a native `property_id` field.

#### Recommended Mapping Strategy

**Use QuickBooks `Class` to represent properties:**

```cypher
// Neo4j: Store QB Class mapping
CREATE (prop:Property {
  property_id: "prop_oak_street",
  qb_class_id: "10",           // QuickBooks ClassRef.value
  qb_class_name: "Oak Street Apartments"
})
```

**Query expenses by Class:**

```python
await stargate.execute_tool(
    capability_key="qb.query",
    args={
        "query": "SELECT * FROM Expense WHERE ClassRef = '10'"  # Oak Street property
    },
    org_id=org_id,
    user_id=user_id
)
```

#### Alternative: Use `Department` or `Location`

Some QB setups use:

- **Department:** For properties (Class for business units)
- **Location:** For geographic properties (requires QB Plus/Advanced)

#### Filtering Strategy

```python
async def _fetch_actual_expenses(self, property_id: str, ...):
    # Step 1: Get QB Class ID from Neo4j
    neo4j_result = await self.neo4j.execute_query("""
        MATCH (prop:Property {property_id: $property_id})
        RETURN prop.qb_class_id as class_id
    """, property_id=property_id)

    qb_class_id = neo4j_result[0]['class_id']

    # Step 2: Query QB with Class filter
    response = await self.stargate.execute_tool(
        capability_key="qb.query",
        args={
            "query": f"SELECT * FROM Expense WHERE ClassRef = '{qb_class_id}' AND TxnDate >= '{start_date}'"
        },
        org_id=org_id,
        user_id=user_id
    )

    expenses = response.result['results'].get('Expense', [])
```

#### Category Mapping

**QuickBooks uses `AccountRef` for expense categories:**

```python
# Map QB Account to expense category
category_mapping = {
    "67": "HVAC Repairs",        # Account ID 67 = Repairs & Maintenance
    "68": "Plumbing",
    "69": "Electrical",
    "70": "Landscaping",
    "85": "Legal Fees"
}

# Or fetch from Chart of Accounts
coa_response = await stargate.execute_tool(
    capability_key="chartofaccounts.get",
    args={},
    org_id=org_id,
    user_id=user_id
)
```

---

### Multi-Tenant Credential Management

**Credential Isolation:** `{org_id}:{user_id}:{service}`

#### How It Works

```python
# Storage (handled by stargate-lite internally)
CredentialManager.store_credential(
    org_id="org_12345",
    user_id="user_67890",
    service="quickbooks",
    access_token="eyJ...",         # Encrypted at rest (Fernet)
    refresh_token="1//...",         # Encrypted at rest
    token_expiry=datetime(...),
    realm_id="9130123456789"        # QB company ID
)

# Retrieval (automatic in connectors)
cred = CredentialManager.get_credential(
    org_id="org_12345",
    user_id="user_67890",
    service="quickbooks"
)
# Returns: {access_token, refresh_token, token_expiry, realm_id}
```

#### Token Refresh (Automatic)

Stargate-lite **automatically refreshes** OAuth tokens if:

- Token is expired OR
- Token expires within 5 minutes

**MARS does NOT need to handle token refresh.** Just call the capability.

---

### Recommended Code Updates

#### Update: `_fetch_actual_expenses()` (Line 425)

**BEFORE:**

```python
response = await self.stargate.execute_tool(
    tool_name="quickbooks.query_entities",  # WRONG: tool_name doesn't exist
    args={
        "entity": "Expense",                  # WRONG: not a valid arg
        "query": f"WHERE TxnDate >= '{start_date}'",  # WRONG: missing SELECT
        "max_results": 1000
    },
    ...
)
```

**AFTER:**

```python
# Step 1: Get QB Class ID for property
class_mapping = await self.neo4j.execute_query("""
    MATCH (prop:Property {property_id: $property_id})
    RETURN prop.qb_class_id as class_id
""", property_id=property_id)

qb_class_id = class_mapping[0]['class_id'] if class_mapping else None

if not qb_class_id:
    logger.error(f"No QuickBooks Class mapping for property {property_id}")
    return 0.0

# Step 2: Query QuickBooks expenses
response = await self.stargate.execute_tool(
    capability_key="qb.query",              # CORRECT: capability_key
    args={
        "query": f"SELECT * FROM Expense WHERE ClassRef = '{qb_class_id}' AND TxnDate >= '{start_date}' AND TxnDate < '{end_date}'"
    },
    org_id=org_id,
    user_id=user_id
)

if not response.ok:
    logger.error(f"Stargate error: {response.result}")
    return 0.0

expenses = response.result.get('results', {}).get('Expense', [])

# Step 3: Filter by category (AccountRef)
category_account_mapping = await self._get_category_account_mapping(org_id)
account_id = category_account_mapping.get(category)

if account_id:
    expenses = [e for e in expenses if e.get('AccountRef', {}).get('value') == account_id]

total = sum([float(e.get('Amount', 0.0)) for e in expenses])
```

#### Add: Category-to-Account Mapping

```python
async def _get_category_account_mapping(self, org_id: str) -> Dict[str, str]:
    """
    Fetch category → QuickBooks Account ID mapping from Neo4j

    Example:
    "HVAC Repairs" → "67" (Account ID in QB)
    """
    query = """
    MATCH (org:Organization {org_id: $org_id})
    MATCH (org)-[:HAS_KNOWLEDGE]->(k:Knowledge)
    WHERE k.knowledge_type = 'qb_category_mapping'
    RETURN k.category as category, k.qb_account_id as account_id
    """

    results = await self.neo4j.execute_query(query, org_id=org_id)

    return {r['category']: r['account_id'] for r in results}
```

---

### Budget Source (Answer to Question 4)

**Option 1: QuickBooks Budget Entity (Recommended if available)**

```python
response = await self.stargate.execute_tool(
    capability_key="budget.get",
    args={
        "budget_name": "2024 Annual Budget"  # Or budget_id
    },
    org_id=org_id,
    user_id=user_id
)

budget_data = response.result
# Returns: Budget by account/class/month
```

**Option 2: Neo4j Knowledge (Fallback)**

```cypher
CREATE (k:Knowledge {
  knowledge_id: "budget_oak_hvac_2024_10",
  org_id: "org_12345",
  knowledge_type: "budget",
  property_id: "prop_oak_street",
  category: "HVAC Repairs",
  month: "2024-10",
  amount: 8500.00,
  confidence: 0.95,
  source: "manual_entry",
  last_updated: datetime()
})
```

**Hybrid Approach (Best):**

1. Try `budget.get` capability from QuickBooks
2. If not available, fetch from Neo4j Knowledge
3. If missing, use historical average as fallback

---

### Metric Caching Strategy (Answer to Question 3)

**Recommended Schedule:**

1. **Monthly aggregation:** 1st of month at 2am (cache prior month)
2. **Weekly refresh:** Every Monday at 3am (update current month-to-date)
3. **On-demand:** When variance analysis detects gaps

#### Cache Node Structure

```cypher
CREATE (m:Metric {
  metric_id: "metric_oak_hvac_2024_10",
  org_id: "org_12345",
  property_id: "prop_oak_street",
  metric_type: "expense_total",
  category: "HVAC Repairs",
  month: "2024-10",
  total_amount: 12847.50,
  transaction_count: 3,
  qb_account_id: "67",           // QB Account reference
  qb_class_id: "10",             // QB Class reference
  last_updated: datetime(),
  source: "quickbooks_sync"
})
```

---

### Updated Usage Example

```python
# CORRECT stargate-lite usage for financial analytics
from aleq_mind.connectors.stargate_client import get_stargate_client

stargate = get_stargate_client()

# Query October expenses for Oak Street property
response = await stargate.execute_tool(
    capability_key="qb.query",
    args={
        "query": "SELECT * FROM Expense WHERE ClassRef = '10' AND TxnDate >= '2024-10-01' AND TxnDate <= '2024-10-31'"
    },
    org_id="org_12345",
    user_id="user_67890"
)

if response.ok:
    expenses = response.result['results'].get('Expense', [])
    total = sum([float(e['Amount']) for e in expenses])
    print(f"Total October expenses: ${total:,.2f}")
else:
    print(f"Error: {response.result}")
```

---

### Key Takeaways

1. ✅ Use `capability_key` not `tool_name`
2. ✅ QB query syntax: `SELECT * FROM Entity WHERE ...`
3. ✅ Map properties via QuickBooks `Class` (store in Neo4j)
4. ✅ Map categories via QuickBooks `Account` (Chart of Accounts)
5. ✅ Stargate handles OAuth token refresh automatically
6. ✅ Max 1000 results per query (implement pagination if needed)
7. ✅ No aggregations in QB queries - aggregate client-side
8. ✅ Cache monthly metrics in Neo4j to reduce API calls
9. ✅ Use `budget.get` capability for variance analysis
10. ✅ All OAuth credentials encrypted at rest (Fernet)
