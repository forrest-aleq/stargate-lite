# Contract B: Task Information Sufficiency

## Relationship to Contract A

Contract A (see `information-sufficiency-contract.md`) covers the **chat path** — user is present, Aleq asks targeted clarification questions inline, tight synchronous loop.

Contract B covers the **task path** — user may not be present. A task was spawned and needs to execute. If information is insufficient, Aleq can't just ask a follow-up in a conversation that may have moved on.

**Shared**: `compute_slot_coverage()` — same function, same assessment, same capability schemas from Stargate.

**Different**: everything about how "not enough information" gets resolved.

---

## The Problem

Tasks come from everywhere:

| Entry Point | Example | Starting Coverage |
|---|---|---|
| Conversation spawn | "Run AP triage" → background task | Medium — some context from the message |
| Slack trigger | New message in #invoices | Low — just a signal, few details |
| Email trigger | Invoice PDF arrives | Medium — attachment has data, but no instructions |
| Scheduled | Monday 9am covenant check | High — recurring, patterns learned |
| Child agent (Paper #23) | Parent spawns sub-task | Inherited — parent passes filled slots |
| ClickUp/Monday task | Status change fires webhook | Medium — task fields pre-fill some slots |

In chat, the user is **right there**. Asking a question is natural and fast.

In tasks, every pause is **friction**. The user might be in a meeting. The task might have been auto-triggered. A task that pauses to ask for a slot the belief graph already knows is a bad experience.

Tasks must **try harder to self-resolve** before involving the user.

---

## The Pre-Fill Cascade

Before declaring information insufficient, tasks run through four sources in order. Each source can fill slots. After each source, coverage is recomputed. If threshold is met at any point, skip the rest and execute.

```
Task spawned with capability keys + initial context
    ↓
┌─ Source 1: Spawning Context ─────────────────────────────────┐
│  Extract slot values from the message/event that created     │
│  the task. TaskSpec.clarifications may already have answers.  │
│  Coverage recompute → threshold met? → EXECUTE               │
└──────────────────────────────────────────────────────────────┘
    ↓ (still insufficient)
┌─ Source 2: Belief Graph (Neo4j L1/L2/L3) ───────────────────┐
│  Query org beliefs for slot-relevant values.                  │
│  "This org uses NET_30" (strength 0.85) → fill payment_terms │
│  Strength > 0.5 → pre-fill. Strength < 0.5 → skip.          │
│  Coverage recompute → threshold met? → EXECUTE               │
└──────────────────────────────────────────────────────────────┘
    ↓ (still insufficient)
┌─ Source 3: Temporal Patterns (Paper #25) ────────────────────┐
│  Check learned patterns for this capability + time context.   │
│  "Last 4 Mondays, user ran this with date_range=last_week"   │
│  Pattern confidence > 0.6 → pre-fill.                        │
│  Coverage recompute → threshold met? → EXECUTE               │
└──────────────────────────────────────────────────────────────┘
    ↓ (still insufficient)
┌─ Source 4: Workflow Hints (Stargate schema) ─────────────────┐
│  Check CapabilitySchema.workflow.typically_preceded_by.        │
│  If a preceding capability already ran in this session,       │
│  its outputs may fill this capability's inputs.               │
│  e.g., vendor.search returned vendor_id → vendor.create      │
│  gets vendor_id pre-filled.                                   │
│  Coverage recompute → threshold met? → EXECUTE               │
└──────────────────────────────────────────────────────────────┘
    ↓ (STILL insufficient after all sources)
    PAUSE task → create Information Request
```

### Why this order matters

1. **Spawning context** is free — already in memory, no I/O.
2. **Beliefs** are fast — L1 cache is in-memory, L2 is Redis. Only L3 (Neo4j) hits disk.
3. **Temporal patterns** require a query but are pre-computed (nightly detection, Paper #25).
4. **Workflow hints** require checking session history — slightly more expensive.

Each source is progressively more expensive. Stop as soon as coverage is met.

---

## Task States and Information Requests

### Current task lifecycle (already implemented)

```
PENDING → RUNNING → COMPLETE
                  → FAILED
                  → CANCELLED
```

### Extended with information sufficiency

```
PENDING → RUNNING → COMPLETE
    ↓               → FAILED
    ↓               → CANCELLED
    ↓
NEEDS_INFO → (user provides) → RUNNING → ...
```

`NEEDS_INFO` is a new task state. The task is not failed — it's paused, waiting for specific information. It can be resumed once the missing slots are filled.

### Information Request

When a task enters `NEEDS_INFO`, it publishes an **Information Request** — a structured object describing exactly what's missing:

```python
class InformationRequest:
    task_id: str
    capability_key: str
    missing_slots: list[MissingSlot]  # Same type as Contract A
    coverage: float                    # Current coverage (0.0-1.0)
    pre_fill_sources_tried: list[str]  # ["context", "beliefs", "patterns", "workflow"]
    generated_questions: list[str]     # Natural language questions from schemas
    priority: TaskPriority             # Inherited from task
    created_at: str                    # ISO timestamp
    expires_at: str | None             # Optional deadline (from task timeout)
```

Each `MissingSlot` carries the schema metadata (type, description, example, enum) so the frontend can render rich input fields, not just a text box.

---

## How the Frontend Handles It

The frontend already has the infrastructure. The wiring:

### Task dot changes color
Task dots in the navbar are 7x7px, color-coded by status. Add a color for `NEEDS_INFO`:

| Status | Color | Meaning |
|---|---|---|
| PENDING | gray | Queued |
| RUNNING | blue | Executing |
| COMPLETE | green | Done |
| FAILED | red | Error |
| NEEDS_INFO | **amber** | Waiting for user input |

### Task panel shows missing slots
When the user clicks the amber dot, the task panel opens showing:
- Task description
- What it was trying to do (capability + filled slots so far)
- Specific missing slots with schema-driven input fields
- Pre-fill sources that were already tried ("Checked beliefs: no match")

### Approval dialog reuse
The existing approval dialog (supervision mode, confidence, countdown timer) can be extended for information requests. Instead of "Approve this action?", it shows "This task needs information to continue" with the specific questions.

### SSE event

```python
# Published when task enters NEEDS_INFO
event: task_needs_info
data: {
    "task_id": "...",
    "capability_key": "vendor.create",
    "missing_slots": [
        {
            "parameter": "vendor_name",
            "type": "string",
            "required": true,
            "description": "Display name for the vendor",
            "example": "Acme Supply Co.",
            "question": "What's the vendor name? (e.g., Acme Supply Co.)"
        }
    ],
    "coverage": 0.6,
    "priority": "normal"
}
```

### User provides info → task resumes

```python
# User fills in the missing slot via frontend
POST /api/v1/tasks/{task_id}/provide_info
{
    "slots": {
        "vendor_name": "Acme Supply Co."
    }
}

# Task supervisor:
# 1. Fills slots into TaskSpec.clarifications
# 2. Recomputes coverage
# 3. If threshold met → transition to RUNNING, resume execution
# 4. If still insufficient → update InformationRequest with remaining gaps
```

---

## Trust Interaction

Trust affects tasks differently than chat:

### Coverage threshold (same as Contract A)
```
effective_threshold = base_threshold - (trust_level * 0.15)
```

Higher trust → lower threshold → fewer pauses.

### Pre-fill aggressiveness
Trust affects how readily beliefs are used to fill slots:

```
# Low trust (0.3): only use strong beliefs
belief_fill_threshold = 0.7 - (trust_level * 0.3)
# At trust=0.3: need belief strength > 0.61 to pre-fill
# At trust=0.7: need belief strength > 0.49 to pre-fill
# At trust=1.0: need belief strength > 0.40 to pre-fill
```

A trusted Aleq fills more aggressively from beliefs. An untrusted Aleq only uses high-confidence beliefs, pauses more often.

### Autonomy after info is filled
Once all slots are filled (through pre-fill or user input), the trust-gated autonomy decision from Contract A still applies. Filled slots → coverage met → but does Aleq execute autonomously or propose?

```
Task slot coverage ≥ threshold
    ↓
effective_strength = min(belief_strength, trust_ceiling)
    ↓
effective_strength ≥ hitl_threshold → execute silently
effective_strength < hitl_threshold → execute but notify user after
```

Note: tasks that were explicitly spawned from a user request ("run AP triage") carry implicit approval. The autonomy check matters more for trigger-spawned and schedule-spawned tasks where the user didn't directly ask.

---

## Multi-Agent Composition (Paper #23)

When a parent agent spawns child agents, information sufficiency cascades:

### Parent fills what it can
The parent agent's work unit may have 5 required slots. It fills 3 from the conversation. It spawns child agents for the remaining work, passing its filled slots as context.

### Children inherit and extend
Each child gets the parent's filled slots plus its own capability schema. A child for `vendor.create` inherits `org_id` and `user_id` from the parent but still needs `vendor_name` for its specific capability.

### Children's information requests bubble up
If a child enters `NEEDS_INFO`, the parent agent is notified. The parent can:
1. Fill from its own context (it knows things the child doesn't)
2. Ask the user on behalf of the child (batching questions from multiple children)
3. Pause its own execution until the child resolves

### Batched questions
If 3 children are each missing one slot, the parent batches them into one user-facing question set instead of 3 separate interrupts:

```
Task "AP Triage" needs information to continue:

1. For vendor creation: What's the vendor name?
2. For bill posting: Which GL account? (6100-Operating, 6200-Admin, 6300-Marketing)
3. For payment scheduling: Payment date? (e.g., 2026-02-15)
```

One interrupt, three slots filled, three children resume.

---

## Comparison: Contract A vs Contract B

| Aspect | Contract A (Chat) | Contract B (Task) |
|---|---|---|
| **User present?** | Yes, always | Maybe not |
| **Assessment** | `compute_slot_coverage()` | Same function |
| **Resolution** | Ask inline | Pre-fill cascade, then pause |
| **Pre-fill effort** | Minimal (context only) | Maximum (context → beliefs → patterns → workflow) |
| **Question delivery** | Chat message | SSE event → task panel / approval dialog |
| **Answer delivery** | Next chat message | `POST /tasks/{id}/provide_info` |
| **Latency tolerance** | Low (user waiting) | High (async, can wait) |
| **Trust effect** | Threshold + autonomy | Threshold + pre-fill aggressiveness + autonomy |
| **Multi-agent** | N/A (single thread) | Parent batches children's requests |

---

## Implementation: Baby MARS

### New code

| Component | File | Change | Size |
|---|---|---|---|
| NEEDS_INFO state | `src/tasks/models.py` | Add `NEEDS_INFO` to TaskStatus enum | ~2 lines |
| InformationRequest | `src/tasks/models.py` | New dataclass for structured info requests | ~15 lines |
| Pre-fill cascade | `src/tasks/prefill.py` (new) | Ordered resolution: context → beliefs → patterns → workflow | ~60 lines |
| Task supervisor wiring | `src/tasks/registry.py` | Before execution, run pre-fill cascade + coverage check | ~20 lines |
| SSE event | `src/tasks/registry.py` | Publish `task_needs_info` event with missing slots | ~10 lines |
| Provide info endpoint | `src/api/routes/tasks.py` | `POST /tasks/{id}/provide_info` → fill slots → resume | ~25 lines |
| Belief slot query | `src/tasks/prefill.py` | Query BeliefGraphManager for slot-relevant beliefs | ~15 lines |
| Pattern slot query | `src/tasks/prefill.py` | Query pattern detector for recurring slot values | ~15 lines |

**Total: ~160 lines of new code, ~30 lines of modifications**

### Contract Tests

| Test | What it validates |
|---|---|
| `test_prefill_context_fills_slots` | Spawning context extracted into slot values |
| `test_prefill_beliefs_strong` | Strong belief (>threshold) pre-fills slot |
| `test_prefill_beliefs_weak_skipped` | Weak belief leaves slot missing |
| `test_prefill_patterns_confident` | Confident temporal pattern pre-fills slot |
| `test_prefill_cascade_stops_early` | Execution starts as soon as threshold met (doesn't run remaining sources) |
| `test_prefill_cascade_all_sources` | All 4 sources tried when each is insufficient alone |
| `test_needs_info_state_transition` | Task transitions PENDING → NEEDS_INFO when insufficient |
| `test_needs_info_sse_event` | SSE publishes correct missing slots with schema metadata |
| `test_provide_info_resumes_task` | Filling missing slots via API resumes task to RUNNING |
| `test_provide_info_still_insufficient` | Partial fill keeps task in NEEDS_INFO with updated gaps |
| `test_trust_affects_belief_threshold` | Higher trust → lower belief strength needed for pre-fill |
| `test_trigger_spawned_low_coverage` | Slack/email trigger starts with low coverage, hits pre-fill |
| `test_scheduled_task_high_coverage` | Scheduled task with patterns starts with high coverage |
| `test_child_agent_inherits_slots` | Child receives parent's filled slots as starting context |
| `test_parent_batches_child_requests` | Multiple children's info requests batched into one |

---

## Contract Interface

### Task spawn (existing, extended)
```python
TaskSpec {
    intent: str
    description: str
    capabilities: list[str]
    context_key: str
    clarifications: dict[str, Any]    # ← slots filled here
    original_message: str
    priority: TaskPriority
    timeout_seconds: int

    # NEW
    pre_filled_slots: dict[str, SlotFill]  # source-tagged fills
    coverage_at_spawn: float               # coverage when spawned
    spawned_from: str                      # "conversation" | "trigger" | "schedule" | "agent"
}

SlotFill {
    value: Any
    source: "conversation" | "belief" | "pattern" | "workflow" | "user" | "parent_agent"
    confidence: float          # belief strength, pattern confidence, or 1.0 for explicit
    belief_id: str | None      # if source is belief
}
```

### Information request (new)
```python
# SSE event
event: task_needs_info
data: InformationRequest {
    task_id: str
    capability_key: str
    missing_slots: list[MissingSlot]
    coverage: float
    pre_fill_sources_tried: list[str]
    generated_questions: list[str]
    priority: TaskPriority
    created_at: str
    expires_at: str | None
}

# Resolution endpoint
POST /api/v1/tasks/{task_id}/provide_info
← { slots: Record<string, Any> }
→ { task_id, new_coverage, status: "running" | "needs_info", remaining_slots? }
```

### Stargate execution (existing, unchanged)
```python
POST /api/v1/execute
← {
    capability_key: str
    org_id: str
    user_id: str
    args: Record<string, Any>   # all required slots guaranteed filled
    turn_id: str
    session_id: str
}
```

Stargate never sees an incomplete request. Contract B catches it first.

---

## Order of Operations

1. **Contract A first** — chat path proves slot coverage computation and targeted questions work
2. **Contract B: pre-fill cascade** — add belief and pattern slot filling for tasks
3. **Contract B: NEEDS_INFO state** — task pausing and SSE notification
4. **Contract B: provide_info endpoint** — user fills slots, task resumes
5. **Contract B: trust-gated pre-fill** — trust level affects belief fill aggressiveness
6. **Paper #23 composition** — parent/child slot inheritance and batched questions

Steps 1-4 are the contract. Steps 5-6 are composition with trust-gating and multi-agent.
