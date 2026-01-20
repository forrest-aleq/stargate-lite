# Terminal Depth Analysis: The CFO's Thinking Substrate

## The Excel Parallel

Excel succeeded not as a spreadsheet, but as an **externalized cognitive architecture**. The grid hijacked the brain's spatial navigation system (grid cells in the entorhinal cortex). Data became *locational* - Revenue is "top-left," not an abstract number.

This spatial anchoring freed working memory. The screen held the structure; the brain focused on relationships.

The keyboard mastery wasn't about speed - it was about **flow state**. When motor memory executes without conscious thought, the interface becomes invisible. Users experience direct manipulation of their mental model.

Aleq's terminal must capture this same psychological space - but with natural language instead of formulas, and AI instead of manual calculation.

---

## The CFO's Morning Question

Every CFO wakes up with uncertainty. A question. This is the "Fear Zone" - they don't know something they need to know.

The terminal is where they express that uncertainty.
The canvas is where answers become spatial anchors - landmarks in their cognitive map.

---

## Usage Pattern Taxonomy

### 1. The Uncertainty Reduction Loop

```
CFO: "Why is cash down?"
Aleq: "Cash dropped $84K this week. Main driver: the $67K payment to [Vendor X]
       plus three smaller outflows. Revenue deposits were $12K below forecast."
CFO: "Show me that vendor"
Aleq: [drills into Vendor X - payment history, terms, relationship]
CFO: "What if we delayed their payment 30 days?"
Aleq: "Cash would be $67K higher. No late penalty until day 45.
       Your relationship score with them is 'Good' - one delay unlikely to damage it."
CFO: *relief - has control*
```

**What this requires from backend:**
- Transaction-level drill-down
- Entity profiles (vendors, customers)
- Scenario engine for "what if"
- Relationship/behavioral data (payment patterns)

---

### 2. The Spatial Anchoring Pattern

```
CFO: "What's our AR situation?"
Aleq: [shows AR data]
CFO: "Put that on the canvas"
→ AR widget appears, becomes a LOCATION
CFO: "Now show me cash"
→ Cash widget appears, another LOCATION
CFO: "How does @ar affect @cash?"
Aleq: [explains relationship, shows conversion timeline]
```

The CFO now has a cognitive map:
- AR is "right side"
- Cash is "left side"
- They can reference these spatially in future queries

**What this requires from backend:**
- Widget instantiation API
- Cross-widget relationship engine
- Ability to explain causality between metrics

---

### 3. The Progressive Disclosure Pattern (Excel Drill-Down)

```
CFO: "What's our biggest expense?"
Aleq: "Payroll at $892K - 68% of total operating expenses"
CFO: "Break that down"
Aleq: "Engineering: $534K (60%), Sales: $223K (25%), G&A: $135K (15%)"
CFO: "Drill into engineering"
Aleq: "12 FTEs. Top 3: [Senior Eng $185K], [Senior Eng $178K], [Staff Eng $165K]..."
CFO: "Add [Senior Eng 1] to context"
→ pill appears: "Alex Chen - $185K"
CFO: "When did they start? What's their equity?"
Aleq: [pulls from HR data]
```

This is exactly like double-clicking a pivot cell to see underlying records.

**What this requires from backend:**
- Hierarchical entity data (category → subcategory → individual)
- Cross-system entity resolution (Finance → HR)
- Full entity profiles, not just financial summaries

---

### 4. The Scenario Modeling Pattern

```
CFO: "if we lose Acme, what happens to revenue?"
Aleq: "Revenue drops 18%. Acme is $267K ARR, your second-largest customer."
CFO: "and if we also cut marketing by 20%?"
Aleq: "Net impact: -$312K revenue (accounting for reduced CAC payback)"
CFO: "show me runway in both scenarios"
Aleq: "Current: 14 months. Lose Acme: 11 months. Lose Acme + cut marketing: 12.5 months"
CFO: "What if we backfill Acme with two mid-market deals?"
Aleq: "Based on your current pipeline, 40% probability you close $150K+ in 90 days..."
```

This is Excel's goal-seek and scenario manager, but conversational.

**What this requires from backend:**
- Scenario engine that can:
  - Accept arbitrary conditions
  - Chain/compound conditions
  - Run sensitivities
  - Access pipeline data (probabilistic)
- Causal model of the business (what affects what)

---

### 5. The Temporal Pattern

```
CFO: "What was cash last Monday?"
Aleq: "$1.163M - $84K less than today"
CFO: "What changed?"
Aleq: "Major inflows: $47K from [Customer], $23K from [Customer].
       Major outflows: $67K to [Vendor], $38K payroll run."
CFO: "Show me the trend for the month"
Aleq: [sparkline or narrative of cash movement]
CFO: "if this trend continues, what's runway in 90 days?"
Aleq: "Extrapolating current burn trajectory: 11.2 months runway by end of Q1"
```

**What this requires from backend:**
- Point-in-time snapshots: `GET /api/widgets/cash?at=2024-12-23`
- Time series: `GET /api/widgets/cash?range=last_30_days`
- Change detection: `GET /api/diff/cash?from=2024-12-01&to=2024-12-29`
- Trend extrapolation engine

---

### 6. The Audit Pattern (Show Your Work)

```
CFO: "How did you calculate runway?"
Aleq: "Current cash: $1.247M (from Mercury, synced 2h ago)
       Monthly burn: $89K (average of last 3 months: $92K, $87K, $88K)
       Runway = Cash / Burn = 14.0 months
       Zero-cash date: March 2026"
CFO: "The burn seems low - we hired two people last month"
Aleq: "You're right. If I include projected salary for new hires ($24K/mo combined),
       burn becomes $113K, runway becomes 11.0 months."
CFO: "Use the adjusted number"
Aleq: "Updated. I'll remember this adjustment going forward."
```

This is like clicking into a cell to see the formula.

**What this requires from backend:**
- Calculation chain visibility
- Source attribution for every number
- User correction/override mechanism
- Persistent memory of corrections

---

### 7. The Correction Pattern

```
CFO: "That $24,800 payment - that wasn't from Acme"
Aleq: "Who was it from?"
CFO: "Beta Corp"
Aleq: "Correcting. This changes:
       - Acme AR: $24,800 still outstanding (was: paid)
       - Beta AR: Cleared (was: $24,800 outstanding)
       - Total AR: unchanged
       Want me to update the source record in QuickBooks?"
CFO: "Yes"
Aleq: [executes correction, logs audit trail]
```

**What this requires from backend:**
- Bi-directional write-back to source systems
- Correction audit trail
- Cascading update engine (what else changes when this changes)

---

### 8. The Cross-Reference Pattern

```
CFO: "@cash @ar @runway - summarize my position"
Aleq: "Cash: $1.247M (+7% MoM) - healthy
       AR: $342K outstanding, $47K overdue (Acme 12 days, TechFlow 8 days)
       Runway: 14 months at current burn

       Key insight: If Acme and TechFlow pay this week, cash goes to $1.3M+
       and runway extends to 15.2 months."
```

**What this requires from backend:**
- Multi-widget context synthesis
- Cross-entity causality (AR → Cash → Runway chain)
- Insight generation from combined data

---

### 9. The Compound Conditional Pattern

```
CFO: "if Acme churns AND we raise Series B at $5M, what's our runway?"
Aleq: "Acme churn: -$267K ARR, burn increases to $102K/mo
       Series B: +$5M cash
       Net: Runway extends from 14 months to 52 months

       But: Losing Acme might affect Series B terms.
       Your revenue concentration becomes a risk factor."
```

**What this requires from backend:**
- Compound scenario engine
- Second-order effect modeling
- Qualitative risk assessment

---

### 10. The "Something's Off" Pattern (Exploratory)

```
CFO: "Something feels wrong with our numbers"
Aleq: "Let me check for anomalies...

       Found 3 items worth reviewing:
       1. Expense spike: AWS costs +340% this month ($2.1K → $9.2K)
       2. Revenue timing: December recognition $34K below December last year
       3. AR aging: TechFlow has gone from 'current' to '30-60 days' for first time

       Want me to dig into any of these?"
```

**What this requires from backend:**
- Anomaly detection engine
- Historical comparison baselines
- Pattern recognition across all data
- Proactive insight surfacing

---

## The Terminal UX Gap Analysis

Current terminal supports:
- `/commands` for actions
- `@references` for entities
- Context pills for accumulated state
- Streaming responses

Missing for true "flow state":

### Keyboard-First Gaps
- **History navigation**: Up/down arrow to recall queries (like shell)
- **Tab completion**: Partial `@ac` → `@Acme Corp`
- **Quick dismiss**: Esc to clear input, not just close autocomplete
- **Context manipulation from keyboard**: Remove pill with `Cmd+Backspace` on it

### Conversational Continuity Gaps
- **Anaphora resolution**: "that" → last mentioned entity
- **Temporal deixis**: "this month", "last week", "yesterday" → resolved correctly
- **Numeric reference**: "the first one", "option 2" → select from list
- **Continuation**: "and also", "but what about" → chain queries

### Output Control Gaps
- **Format requests**: "as a table", "as a chart", "summarize in one line"
- **Persistence**: "pin this to canvas", "save this answer"
- **Export**: "email this to me", "copy as markdown"

### Meta-Interaction Gaps
- **Undo**: "undo that", "go back"
- **Clarification**: "what did you mean by X?"
- **Teach**: "remember that X always means Y for us"

---

## Backend API Gap Analysis

Current CONTRACT.md defines:
- Chat streaming ✓
- Task data ✓
- Widget data (current state) ✓
- Context resolution ✓

Missing for full CFO workflow:

### 1. Temporal Data API
```typescript
// Point-in-time
GET /api/widgets/:id?at=2024-12-15

// Time series
GET /api/widgets/:id?range=last_30_days
GET /api/widgets/:id?from=2024-12-01&to=2024-12-29

// Diff
GET /api/diff/:widgetId?from=...&to=...
```

### 2. Scenario API
```typescript
POST /api/scenarios
{
  conditions: [
    { entity: "customer", id: "acme", change: "churn" },
    { metric: "burn", delta: "+15%" }
  ],
  query: "runway"
}

// Response includes:
// - New calculated values
// - What changed and why
// - Second-order effects
```

### 3. Entity Deep-Dive API
```typescript
GET /api/entities/:type/:id
// Returns full profile, not just financial summary

GET /api/entities/:type/:id/history
// Payment history, interaction log, status changes

GET /api/entities/:type/:id/related
// What widgets/metrics does this entity affect
```

### 4. Relationship/Causality API
```typescript
GET /api/relationships?from=ar&to=cash
// Returns: explanation of how AR flows to Cash

GET /api/causality/:metricId
// Returns: what affects this metric, what this metric affects
```

### 5. Correction/Override API
```typescript
POST /api/corrections
{
  entity: { type: "payment", id: "pmt_123" },
  field: "customer",
  oldValue: "Acme Corp",
  newValue: "Beta Corp",
  reason: "User correction",
  propagate: true  // update downstream calculations
}

GET /api/corrections/history
// Audit trail of all user corrections
```

### 6. Anomaly Detection API
```typescript
GET /api/anomalies
// Returns list of unusual patterns detected

GET /api/anomalies/:id/explain
// Deep explanation of specific anomaly
```

### 7. Memory/Learning API
```typescript
POST /api/memory
{
  type: "preference",
  key: "burn_calculation",
  value: "include_projected_salaries"
}

GET /api/memory?context=runway
// What has user taught us about runway calculations
```

---

## The Psychological Substrate

The Excel document reveals the deep truth: users don't want a tool, they want a **thinking partner**.

Excel gave them:
- Spatial anchoring (data has location)
- Immediate feedback (change → result)
- Incremental complexity (start simple, add depth)
- Control illusion (I understand my business)
- Flow state (interface disappears)

Aleq must give them:
- Spatial anchoring → **Widgets as landmarks**
- Immediate feedback → **Streaming responses, instant answers**
- Incremental complexity → **Progressive drill-down, follow-up questions**
- Control illusion → **"Show your work", corrections respected**
- Flow state → **Keyboard-first, conversational continuity**

The terminal is not a search box. It's not a command line.

It's a **conversation with your own data** - where every question reduces uncertainty, every answer becomes a landmark, and the CFO gradually builds a mental model of their business that they can navigate as naturally as walking through their office.

---

## Priority Implementation Order

1. **Temporal data** - CFOs always ask "compared to when?"
2. **Scenario engine** - "what if" is the core value proposition
3. **Entity deep-dive** - drill-down is how trust is built
4. **Correction mechanism** - Aleq must be correctable to be trusted
5. **Anomaly detection** - proactive insight is the magic moment
6. **Memory/learning** - personalization creates stickiness

The canvas is blank paper.
The terminal is a pen that writes back.
Together, they're the CFO's externalized mind.
