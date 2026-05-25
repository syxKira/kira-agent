## Context

Stages 01-08 made Kira usable as a local web agent: provider selection and fixture fallback, local tools, skill-driven graph runs, durable replay, HITL resume, project retrieval, memory, transcript continuity, compaction, replacement stubs, and fork/rollback now exist. The current system is functional but safety decisions are spread across services and diagnostics are mostly implicit in state/replay endpoints.

Stage 09 introduces a cross-cutting safety and observability layer while preserving the existing `server/`, `web/`, and `src/` layout. It must harden local usage without turning Kira into a production multi-user service, adding a general shell, or redesigning the product UI ahead of Stage 10.

## Goals / Non-Goals

**Goals:**

- Provide one permission action model that every safety-sensitive subsystem can call before executing or exposing an action.
- Persist redacted audit records for provider selection, tools, Python execution, graph/HITL lifecycle, skill activation, project retrieval, memory, transcript operations, and branch operations.
- Expose doctor diagnostics for local install readiness, runtime storage, provider config, `rg`, Python, skills, project index, memory, run locks, side-effect ledger, and version metadata.
- Expose redacted trace/export responses that explain why context, providers, tools, retrieval snippets, memories, transcript items, compaction summaries, replacements, and branch decisions were used.
- Add replacement-output inspection policy for retained local debug data without exposing raw secrets.
- Add frontend surfaces that make diagnostics, audit, trace, permission, and safety states inspectable with accessible loading/empty/error handling.
- Add shared schemas and focused tests so Stage 09 behavior can be applied incrementally.

**Non-Goals:**

- No OS sandbox, cloud deployment, production auth, remote team approvals, or signed remote skill system.
- No general shell or project mutation tools.
- No vector retrieval, cloud memory sync, sub-agent orchestration, or business workflow implementation.
- No Stage 10 visual redesign, dark cockpit, task rail overhaul, final branding pass, or screenshot-driven product polish.
- No storage of raw API keys, hidden thinking as assistant answer text, or raw sensitive replacement blobs in frontend-safe exports.

## Decisions

### 1. Central Permission Service With Local Defaults

Create a backend permission service with structured actions such as `provider.override`, `project.read`, `project.search`, `python.run`, `skill.invoke`, `skill.tool_action`, `memory.write`, `memory.lifecycle`, `transcript.archive`, `transcript.delete`, `transcript.compact`, `transcript.branch`, `replacement.inspect`, and `workflow.external_action`.

Each decision returns `allow`, `ask`, or `deny`, plus reasons, redacted subject metadata, and an audit hint. `ask` is represented as structured metadata for the existing HITL path when the action is part of a graph run, and as a frontend-safe response for explicit UI operations.

Alternatives considered:

- Inline checks inside each service: rejected because audit and diagnostics would drift.
- Full policy language engine: deferred because local v0 needs deterministic defaults, not a complex policy DSL.

### 2. Audit Is Append-Only, Redacted, And Local

Add SQLite audit tables owned by Kira runtime storage. Audit records include action, decision, result status, timestamps, thread/conversation/turn IDs, provider/model, skill/workflow/tool, project root/path/citation, memory ID, compaction/replacement/branch IDs, redacted args, output summary, error class, and correlation IDs.

Secrets are redacted before persistence. Audit export reads from the audit table and does not replay providers, tools, retrieval, memory extraction, or graph nodes.

Alternatives considered:

- Derive audit from events/state only: rejected because important permission decisions and preflight diagnostics happen before normal events.
- Store raw inputs for later debugging: rejected because Stage 09's primary purpose is safe local use and redacted export.

### 3. Doctor Diagnostics Are Read-Only And Structured

Add `GET /api/doctor` with optional query flags for deeper checks. Default doctor performs local read-only checks: provider config loaded/key presence without raw key, runtime SQLite availability/migrations, `rg` availability or fallback, Python runtime availability, skill manifest diagnostics, project index health, memory DB health, run lock anomalies, side-effect ledger anomalies, and frontend/backend version metadata.

Optional real provider smoke tests must be explicit and skipped by default when no valid config is available.

Alternatives considered:

- A separate CLI-only doctor: deferred; an API endpoint is enough for frontend and scripted local checks.
- Always call real providers in doctor: rejected because tests and local startup must not require real API keys.

### 4. Trace Export Aggregates Existing Durable Facts

Add trace/export endpoints around existing run state, replay, context trace, provider attempts, retrieval traces, memory citations, transcript traces, compaction/replacement records, branch records, audit records, side-effect ledger, and checkpoints.

Exports are bounded by query parameters and redacted at serialization time. They are read-only: calling export must not advance event streams, run providers, acquire graph locks, trigger retrieval, update memory, or mutate active conversation heads.

Alternatives considered:

- Make replay the only debug export: rejected because replay is run-centric and does not cover cross-run audit, doctor, memory, retrieval, and transcript evidence.

### 5. Replacement Inspection Is Permission-Gated

Stage 08b replacement stubs intentionally do not expose raw retained output. Stage 09 can add local inspection only when a replacement has an allowed retention policy and the permission service returns `allow` or `ask` is approved. The inspection response must include redacted output, hash/reference metadata, omitted count, reason, and audit record ID.

Alternatives considered:

- Keep no inspection endpoint forever: safe but undermines observability for local debugging.
- Expose raw blobs to frontend: rejected because replacement stubs often exist specifically due to size or secret risk.

### 6. Frontend Adds Functional Observability, Not Product Redesign

The workbench adds panels or tabs for doctor status, audit records, trace export, permission decisions, and structured safety errors using the current layout. It must improve empty/loading/error states and keyboard-accessible controls needed to validate Stage 09 flows, but it must not introduce the Stage 10 dark visual redesign.

Alternatives considered:

- Build a polished observability dashboard: deferred to Stage 10 because Stage 09 should focus on behavior and coverage.

## Risks / Trade-offs

- Permission checks become inconsistent across services → Route all safety-sensitive actions through the permission service and add tests for provider, Python, project, skill, memory, transcript, and replacement actions.
- Audit logs accidentally persist secrets → Use central redaction before insert and add no-secret tests across API, replay, audit, trace, memory, and frontend responses.
- Doctor becomes slow or flaky → Make heavy checks opt-in, skip real provider smoke by default, and keep default checks local/read-only.
- Trace export grows unbounded → Add limits, cursor/time filters, and summary-only defaults for large event/tool/retrieval payloads.
- Replacement inspection leaks sensitive data → Require retention policy, permission decision, redaction, and audit record before returning any inspected content.
- Frontend Stage 09 polish overlaps Stage 10 → Keep UI additions functional and restrained; defer dark shell, task rail redesign, and screenshot-driven visual QA.
- Existing tests rely on fixture fallback → Keep fixture provider as deterministic fallback and ensure all new tests pass without a real API key.

## Migration Plan

1. Add idempotent SQLite migrations for audit records, permission decision records if persisted, doctor snapshots if needed, and trace export metadata if needed.
2. Add shared schemas for permission decisions, audit records, doctor diagnostics, trace export, replacement inspection, and smoke fixtures.
3. Implement redaction helpers and apply them before audit/trace/export persistence.
4. Add permission service defaults and wire it into provider selection, Python execution, project tools/retrieval, skill activation/tool dispatch, memory writes/lifecycle, transcript operations, and replacement inspection.
5. Add doctor and export APIs, then frontend clients and panels.
6. Add backend and frontend tests; run OpenSpec validation.

Rollback strategy: migrations are additive. If Stage 09 code is rolled back, existing Stage 01-08 tables remain readable. Audit/diagnostic tables can remain unused without changing run execution semantics.

## Open Questions

- Should permission defaults be configurable in `~/.kira-agent/config.yaml` during Stage 09, or remain code defaults with config left to a later focused change?
- Should audit export be one endpoint with filters or separate endpoints for runs, conversations, memory, and project roots?
- Should replacement inspection store redacted snapshots after first approval, or re-redact from retained local data on every request?
