# E2B Integration Research

Date: 2026-03-27

## Decision

Use E2B as Stargate's sandboxed code and artifact runtime.

Do not use it as a replacement for:
- `baby-mars` orchestration
- `stargate-lite` capability routing
- `Hyperbrowser` browser automation

## Why It Fits

E2B gives us the substrate Aleq is still missing for:
- long-lived sandboxes
- pause and resume
- background code execution
- filesystem-backed artifacts
- warm templates for finance runtimes

That maps directly onto the Baby MARS Papers 23, 24, and 25 work:
- Paper 23: worker execution substrate
- Paper 24: run-control, receipts, and eval visibility
- Paper 25: wake up, continue work, go back to sleep

## Official Capabilities We Should Rely On

From E2B official docs, the features that matter most for Aleq are:
- sandboxes and lifecycle controls
- auto-resume / paused sandboxes
- templates and snapshots
- filesystem access
- commands and background execution
- MCP gateway and desktop sandboxes as later expansion points

Sources:
- https://e2b.dev/docs/sandbox
- https://e2b.dev/docs/sandbox/auto-resume
- https://e2b.dev/docs/sandbox/snapshots
- https://e2b.dev/docs/template/how-it-works
- https://e2b.dev/docs/filesystem
- https://e2b.dev/docs/commands/background
- https://e2b.dev/docs/mcp
- https://e2b.dev/docs/use-cases/computer-use

## Architecture Fit

### `stargate-lite`

Owns the E2B SDK and exposes typed capabilities:
- `sandbox.ensure`
- `sandbox.python.run`
- `sandbox.python.run_background`
- `sandbox.bash.run`
- `sandbox.bash.run_background`
- `sandbox.file.write`
- `sandbox.file.read`
- `sandbox.command.list`
- `sandbox.command.kill`
- `sandbox.pause`
- `sandbox.timeout.set`
- `sandbox.snapshot.create`
- `sandbox.get_info`

Later capabilities should build on top of these:
- `artifact.xlsx.build`
- `artifact.docx.build`
- `artifact.pptx.build`
- `artifact.pdf.build`
- `chart.render`

### `baby-mars`

Should treat E2B as just another capability family.

What Baby MARS needs on top:
- persist `sandbox_id` in durable runs
- resume sandboxes during wakeups
- associate artifacts with run receipts
- decompose longer jobs into sandbox-backed workers

### `Aleq`

Needs frontend surfaces for:
- live run logs
- generated artifacts
- resume status
- sandbox-backed report/model workspaces

## Initial Implementation Scope

Phase 1:
- typed Stargate connector
- capability registry entries
- schema metadata
- tests
- env/config support
- long-running lifecycle controls (background commands, snapshots, timeout updates)

Phase 2:
- Baby MARS run ledger stores `sandbox_id`
- Codex / worker planning can choose sandbox capabilities
- artifact generation family

Phase 3:
- Research workspace uses sandbox files + previews
- Model workspace emits real `xlsx`
- long-running background work resumes cleanly

## Guardrails

- E2B must stay behind Stargate, not be called directly from Aleq
- browser work stays on Hyperbrowser for now
- sandbox IDs must be treated as run-scoped assets
- artifacts must become first-class receipts, not opaque blobs
- pin against the published Python SDK family we actually validated (`e2b>=2.10.2` today),
  not speculative future versions
