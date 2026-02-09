# Financial Command Interface (FCI) - v0 Specification

## The Core Principle

**One input. Everything.**

The terminal is a Do-Engine, not a search engine. It's designed around VERBS, not menus. Type what you want, see it instantly, commit it to your canvas.

Tesla removed every button. We remove every menu.

---

## Part 1: The Primitives

Everything in the FCI is a primitive. No ambiguity. No magic. Explicit syntax, predictable behavior.

### 1.1 Data Primitives (Instant, No AI)

| Syntax | What It Does | Example | Preview Shows |
|--------|--------------|---------|---------------|
| `@widget` | Widget data lookup | `@cash`, `@ar`, `@runway` | Mini widget card with value, trend, sparkline |
| `@entity:name` | Entity lookup | `@customer:acme`, `@vendor:aws` | Entity card with key metrics |
| `@record:id` | Specific record | `@invoice:1234`, `@payment:5678` | Record detail card |
| `@person:name` | Person lookup | `@person:john`, `@person:cfo` | Person card with role, contact |

**Widgets available:**
- `@cash` - Cash & Equivalents
- `@ar` - Accounts Receivable
- `@ap` - Accounts Payable
- `@burn` - Burn Rate
- `@runway` - Runway (months)
- `@revenue` - Revenue
- `@expenses` - Expenses
- `@payroll` - Payroll

**Entity types:**
- `@customer:` - Customer lookup
- `@vendor:` - Vendor lookup
- `@bank:` - Bank account lookup
- `@invoice:` - Invoice lookup
- `@payment:` - Payment lookup
- `@person:` - Person lookup

---

### 1.2 Math Primitives (Instant, Local Calc)

| Syntax | What It Does | Example | Preview Shows |
|--------|--------------|---------|---------------|
| `number op number` | Basic math | `50k + 30k` | `= $80,000` |
| `@ref op @ref` | Reference math | `@cash + @ar` | `= $1.589M ($1.247M + $342K)` |
| `X% of @ref` | Percentage | `20% of @revenue` | `= $53,400` |
| `@ref / @ref` | Ratio | `@cash / @burn` | `= 14.2 months` |
| `@ref vs @ref` | Comparison | `@cash vs @ar` | Delta with direction |

**Number formats accepted:**
- `50000`, `50,000`, `$50,000`
- `50k`, `50K`, `$50k`
- `1.2m`, `1.2M`, `$1.2M`
- `15%`, `0.15`

**Operators:**
- `+` Add
- `-` Subtract
- `*` Multiply
- `/` Divide
- `vs` Compare (shows delta)
- `% of` Percentage of

---

### 1.3 Scenario Primitives (Fast Model Preview)

| Syntax | What It Does | Example | Preview Shows |
|--------|--------------|---------|---------------|
| `if [condition]` | Single scenario | `if burn +20%` | Impact on runway, cash out date |
| `if [A] and [B]` | Compound scenario | `if burn +20% and revenue flat` | Combined impact |

**Condition types:**
- `burn +20%` / `burn -10%` - Percentage change
- `revenue flat` - No change assumption
- `churn = 5%` - Set to value
- `hire 3 eng` - Headcount change
- `@customer:acme churns` - Entity-specific
- `raise $2m` - Cash injection

**Preview shows:**
- Primary metric impact (runway, cash)
- Before/after comparison
- Cash out date shift

---

### 1.4 Time Modifiers

| Syntax | What It Does | Example |
|--------|--------------|---------|
| `last month` | Previous month | `@cash last month` |
| `last week` | Previous week | `@ar last week` |
| `yesterday` | Previous day | `@cash yesterday` |
| `YTD` | Year to date | `@revenue YTD` |
| `Q4 2024` | Specific quarter | `@expenses Q4 2024` |
| `vs last month` | Comparison | `@cash vs last month` |

Time modifiers attach to the preceding reference.

---

### 1.5 Command Primitives (Local Actions)

| Syntax | What It Does |
|--------|--------------|
| `/clear` | Clear terminal history |
| `/help` | Show command reference |
| `/export [format]` | Export canvas to CSV/PDF/Excel |
| `/lock` | Lock terminal position |
| `/unlock` | Unlock terminal position |
| `/position [left/center/right]` | Set terminal position |
| `/mode [note/ambient]` | Switch mode |

---

### 1.6 AI Primitives (Requires @aleq)

| Syntax | What It Does | Example |
|--------|--------------|---------|
| `@aleq [question]` | Ask Aleq anything | `@aleq why is cash down` |
| `@aleq [action]` | Request Aleq do something | `@aleq draft email to acme` |

**@aleq is required for:**
- Natural language questions
- Explanations and diagnostics
- Content generation (emails, reports)
- Complex analysis requiring reasoning

**@aleq is NOT required for:**
- Data lookups (use `@entity`)
- Math (just type it)
- Scenarios (use `if`)
- Commands (use `/command`)

---

### 1.7 Workflow Primitives (Aleq Actions)

When Aleq needs to DO something (not just answer), use workflow commands:

**Accounts Payable:**
| Command | Action | Rich Result |
|---------|--------|-------------|
| `@aleq ap match [PO]` | 3-way match | Match card: PO vs Receipt vs Invoice |
| `@aleq ap quick [vendor] [amount]` | Non-PO invoice | Smart coding form |
| `@aleq vendor status [name]` | Vendor inquiry | Last 10 invoices, payment status |
| `@aleq pay run` | Process payment batch | Cash requirement, validation |
| `@aleq stop pay [check]` | Stop payment | Confirmation modal |

**Accounts Receivable:**
| Command | Action | Rich Result |
|---------|--------|-------------|
| `@aleq inv create [customer]` | Generate invoice | Invoice preview |
| `@aleq cash apply [amount]` | Apply cash receipt | Smart match suggestions |
| `@aleq credit check [customer]` | Credit analysis | Traffic light (Green/Yellow/Red) |
| `@aleq collect list` | Collections worklist | Prioritized overdue list |

**General Ledger:**
| Command | Action | Rich Result |
|---------|--------|-------------|
| `@aleq gl post` | Manual journal entry | Debit/Credit grid |
| `@aleq gl approve` | Approve JE queue | Pending entries list |
| `@aleq recon dashboard` | Reconciliation status | Progress bar, alerts |
| `@aleq close checklist` | Month-end status | Task list with checkboxes |

**Treasury:**
| Command | Action | Rich Result |
|---------|--------|-------------|
| `@aleq cash pos` | Cash position | Hero metric + breakdown by bank/currency |
| `@aleq wire [amount] to [dest]` | Stage wire transfer | MFA + confirmation |
| `@aleq cash cast` | Cash forecast | Inflow/outflow chart |

---

## Part 2: The Interaction Model

### 2.1 The Input Lifecycle

```
TYPE → PREVIEW → COMMIT
```

1. **TYPE**: User types in terminal
2. **PREVIEW**: Fast model shows instant result (before Enter)
3. **COMMIT**: Enter sends to canvas

### 2.2 Key Bindings

| Key | Action |
|-----|--------|
| **Enter** | Commit to canvas |
| **Tab** | Open options menu |
| **Esc** | Clear / dismiss |
| **Space** | Continue expression |
| **Up/Down** | Navigate autocomplete / history |
| **Cmd+K** | Focus terminal (global) |

### 2.3 What Enter Does (Per Primitive)

| Primitive | Enter Action |
|-----------|--------------|
| `@cash` | Pin widget to canvas |
| `@customer:acme` | Pin entity card to canvas |
| `50k + 30k` | Pin result to canvas (as metric pill) |
| `@cash + @ar` | Pin calculation to canvas |
| `if burn +20%` | Expand full scenario analysis |
| `@aleq question` | Stream AI response |
| `@aleq workflow` | Execute workflow, show progress |
| `/command` | Execute command |

### 2.4 What Tab Does (Options Menu)

For `@cash`:
```
┌──────────────────────────┐
│ Pin to Canvas            │
│ Copy Value               │
│ Drill: See accounts      │
│ Compare: vs last month   │
│ Open in Books            │
│ ─────────────────────    │
│ Dismiss                  │
└──────────────────────────┘
```

For `@customer:acme`:
```
┌──────────────────────────┐
│ Pin to Canvas            │
│ View Full Profile        │
│ See Invoices             │
│ See Payment History      │
│ Email Customer           │
│ Open in Books            │
└──────────────────────────┘
```

For `50k + 30k`:
```
┌──────────────────────────┐
│ Pin to Canvas            │
│ Copy Result              │
│ Save as Named Metric     │
└──────────────────────────┘
```

---

## Part 3: The Canvas

The canvas IS the context. Everything you commit goes here.

### 3.1 Canvas Objects

| Object Type | Appearance | Hover Actions |
|-------------|------------|---------------|
| Widget | Full widget card | Drill, Compare, Open in Books |
| Entity Pill | Compact pill with key metric | Expand, Open in Books |
| Calculation | Result with formula | Edit, Copy, Remove |
| Scenario | Scenario summary | Adjust, Expand, Remove |
| AI Response | Text block | Copy, Pin sections |

### 3.2 Canvas Layout

- Auto-layout by default (grid)
- Drag to rearrange
- Widgets take full grid cells
- Pills stack in context area

### 3.3 Canvas Persistence

- Canvas state persists per session
- Can save canvas as "View" for recall
- Export canvas to PDF/Excel

---

## Part 4: The Mode System

### 4.1 Note Mode (Default)

- Aleq is silent
- You work, things appear on canvas
- Must `@aleq` to invoke AI
- Ambient dots **pulsate** for pending Aleq work (non-intrusive)
- Maximum flow state

### 4.2 Ambient Mode

- Aleq is silent UNLESS it needs you
- Ambient dots **flash/notify** when decision required
- Aleq interrupts only for:
  - Decisions it can't make alone
  - Exceptions that need human judgment
  - Completed work that needs review

### 4.3 Conversation Mode

- Every input gets Aleq response
- Traditional chat feel
- Good for onboarding, learning, exploration

### 4.4 Switching Modes

- `/mode note` - Enter note mode
- `/mode ambient` - Enter ambient mode
- `/mode conversation` - Enter conversation mode

---

## Part 5: The Preview System

Powered by fast model (Gemini Flash or equivalent).

### 5.1 Preview Triggers

- Autocomplete suggestions as you type
- Full preview when input is complete/paused

### 5.2 Preview Content

For `@cash`:
```
┌─────────────────────────────┐
│ CASH & EQUIVALENTS          │
│ $1.247M        ↑ 7.2%       │
│ ▁▂▃▄▅▆▇█                    │
│                             │
│ [↵] Pin   [⇥] Options       │
└─────────────────────────────┘
```

For `@cash + @ar`:
```
┌─────────────────────────────┐
│ = $1.589M                   │
│ $1.247M + $342K             │
│                             │
│ [↵] Pin   [⇥] Options       │
└─────────────────────────────┘
```

For `if burn +20%`:
```
┌─────────────────────────────┐
│ SCENARIO: Burn +20%         │
│                             │
│ Runway: 11.4mo (was 14)     │
│ Cash out: Aug 2026          │
│                             │
│ [↵] Analyze   [⇥] Adjust    │
└─────────────────────────────┘
```

### 5.3 Preview Latency Target

- Data lookups: < 100ms
- Math: < 50ms (local)
- Scenarios: < 500ms (fast model)
- AI queries: No preview (streaming on commit)

---

## Part 6: The Ambient Dots

Visual indicator of Aleq's work queue.

### 6.1 Dot States

| State | Visual | Meaning |
|-------|--------|---------|
| Empty | No dots | Aleq idle |
| Working | Pulsing dots | Aleq processing tasks |
| Needs You | Flashing dot | Decision required (Ambient mode only) |
| Complete | Solid dot | Work done, ready for review |

### 6.2 Clicking a Dot

Opens the task panel for that work item:
- See what Aleq did
- Review decisions
- Approve/reject/modify

---

## Part 7: Bare Text & Autocomplete

### 7.1 Bare Text Behavior

If user types without prefix (e.g., `acme`):

```
→ Autocomplete guides to primitive:
  ┌──────────────────────────┐
  │ @customer:Acme Corp      │
  │ @vendor:Acme Supplies    │
  │ @invoice:ACM-1234        │
  │ @aleq tell me about acme │
  └──────────────────────────┘
```

No bare text execution. Must select a primitive.

### 7.2 Autocomplete Priority

1. Exact matches first
2. Recently used
3. Frequently used
4. Alphabetical

---

## Part 8: Error Handling

### 8.1 Unrecognized Input

```
Input: "show me the money"

→ Preview:
  ┌──────────────────────────────────────┐
  │ I don't recognize this pattern.      │
  │                                      │
  │ Did you mean:                        │
  │ • @cash                              │
  │ • @aleq show me the money            │
  └──────────────────────────────────────┘
```

### 8.2 Missing Data

```
Input: @customer:unknown

→ Preview:
  ┌──────────────────────────────────────┐
  │ Customer not found: "unknown"        │
  │                                      │
  │ Search results:                      │
  │ • No matches                         │
  │                                      │
  │ [⇥] Search all entities             │
  └──────────────────────────────────────┘
```

---

## Part 9: Implementation Priority

### P0 - Core Loop
1. Terminal input with autocomplete
2. Data primitive lookups (`@cash`, `@ar`, etc.)
3. Preview cards for widgets
4. Enter = Pin to canvas
5. Canvas renders pinned items

### P1 - Calculator
6. Math expressions (local calc)
7. Reference math (`@cash + @ar`)
8. Result preview

### P2 - Scenarios
9. `if` statement parsing
10. Scenario preview (fast model)
11. Scenario expansion on Enter

### P3 - AI Integration
12. `@aleq` queries
13. Streaming responses
14. Response pinning

### P4 - Workflows
15. Workflow commands (`@aleq ap match`, etc.)
16. Rich result UIs
17. Task panel integration

### P5 - Polish
18. Mode system (Note/Ambient)
19. Ambient dots
20. Full command set (`/export`, etc.)

---

## Part 10: What This Replaces

| Old Way | FCI Way |
|---------|---------|
| Open dashboard, click filters, find metric | `@cash` |
| Open spreadsheet, build formula, calculate | `@cash + @ar` |
| Open scenario tool, input assumptions, run | `if burn +20%` |
| Open ERP, navigate menus, find vendor | `@vendor:acme` |
| Open chat, type question, wait for response | `@aleq why is cash down` |
| Open AP module, find PO, match invoice | `@aleq ap match [PO]` |

**One input. Everything.**

---

## Appendix: Full Primitive Reference

### Data Lookups
```
@cash, @ar, @ap, @burn, @runway, @revenue, @expenses, @payroll
@customer:[name], @vendor:[name], @bank:[name]
@invoice:[id], @payment:[id], @person:[name]
```

### Math
```
50k + 30k
@cash + @ar
@cash - @ap
@revenue * 1.2
@cash / @burn
20% of @revenue
@cash vs @ar
```

### Scenarios
```
if burn +20%
if revenue flat
if churn = 5%
if @customer:acme churns
if hire 3 eng
if raise $2m
if burn +20% and revenue flat
```

### Time
```
last month, last week, yesterday
YTD, MTD, QTD
Q1 2025, Jan 2025
vs last month, vs last year
```

### Commands
```
/clear, /help
/export [csv|pdf|excel]
/lock, /unlock
/position [left|center|right]
/mode [note|ambient|conversation]
```

### AI
```
@aleq [any question]
@aleq why [observation]
@aleq explain [metric]
@aleq draft [content type]
@aleq compare [A] to [B]
```

### Workflows
```
@aleq ap match [PO]
@aleq ap quick [vendor] [amount]
@aleq vendor status [name]
@aleq pay run
@aleq inv create [customer]
@aleq cash apply [amount]
@aleq credit check [customer]
@aleq collect list
@aleq gl post
@aleq recon dashboard
@aleq cash pos
@aleq wire [amount] to [dest]
```

---

*v0 - December 2024*
