## Context

Kira has a Stage 03 graph runtime that can discover workflow-capable skills, compile `StateGraph` workflows, dispatch Stage 02 tools through `ToolNode`, and stream normalized Kira events. That runtime is intentionally process-local: it has no durable checkpointing, no replay, no run locks, no side-effect ledger, and no state projection endpoint. Stage 04 turns the graph runner into a reliable local workflow runtime while keeping production storage, full HITL UI, memory, and project retrieval out of scope.

The reliability model is local-first. SQLite is the durable store, `thread_id` is the stable cursor, and checkpointed graph state is authoritative. Derived projection tables exist for fast UI reads and debug export, but they must be reconstructable from checkpoints, events, attempts, and ledger records.

## Goals / Non-Goals

**Goals:**

- Add Kira-owned SQLite storage and migrations for reliable graph execution.
- Compile graph runs with a SQLite checkpointer and preserve `thread_id` across resume.
- Persist normalized Kira events with monotonic per-run sequence numbers.
- Add state projection and replay/debug export APIs.
- Add run locks, heartbeat, stale-lock handling, duplicate executor protection, cancellation, and graceful shutdown.
- Add retry/timeout policy, failure taxonomy, provider attempt records, and side-effect idempotency ledger.
- Keep provider secrets redacted in checkpoints, projections, replay, diagnostics, and frontend payloads.

**Non-Goals:**

- No production multi-user database or distributed worker queue.
- No exactly-once guarantee for external systems that do not support idempotency.
- No Stage 05 HITL frontend approval/edit panels.
- No Stage 06 project knowledge retrieval index or ContextItem injection.
- No Stage 07 memory records or extraction.
- No project mutation tools and no general shell tool.

## Decisions

### Decision: Add a dedicated local storage layer

Create `server/src/kira_server/storage/` for SQLite connection policy, migrations, repositories, and test helpers. The default database path should live under Kira-owned user-local storage, not the project root. Tests can override the path with a temporary database.

Rationale: Reliability concerns cut across graph execution, events, locks, attempts, and replay. A dedicated storage layer prevents these concerns from leaking into API routes.

Alternative considered: Store everything in the existing in-memory run store. That cannot survive process restart and cannot support replay or lock correctness.

### Decision: Checkpointed state is authoritative, projections are derived

LangGraph checkpoint state is the source of truth for graph continuation. Kira tables such as `run_events`, `run_attempts`, `provider_attempts`, `side_effect_ledger`, `run_locks`, and `repair_notes` provide UI projection, replay, diagnostics, and reliability policy.

Rationale: This follows durable workflow practice: use checkpoint state for execution and derived tables for product inspection.

Alternative considered: Treat projection tables as the primary state. That would duplicate LangGraph state semantics and increase corruption risk.

### Decision: Persist events before streaming them

Graph events should be written to `run_events` with the next per-thread sequence before they are sent over SSE. SSE reconnect uses a cursor to replay stored events before following live events.

Rationale: UI state and debug replay need stable sequence numbers. Streaming first risks gaps if the process exits before persistence.

Alternative considered: Continue generating sequence numbers in memory. That breaks reconnect and replay.

### Decision: One active executor per `thread_id`

Run/resume execution must acquire a `run_locks` row with owner, heartbeat, and expiry. Duplicate execution attempts return current state or a structured conflict. Stale locks can be taken over only after recording takeover metadata.

Rationale: Duplicate graph runners are the fastest way to duplicate tools, provider calls, and side effects.

Alternative considered: Let LangGraph checkpointer serialize execution. The checkpointer persists state, but Kira still needs product-level ownership and conflict behavior.

### Decision: Ledger all side-effect-capable calls

Every graph tool call receives an idempotency key derived from thread, checkpoint, node, call index, tool name, and argument hash. Completed ledger entries are reused on resume/replay; unknown entries require repair or reconciliation.

Rationale: Replay must be read-only by default and resume must avoid duplicating external actions.

Alternative considered: Only ledger external tools later. That would require changing ToolNode dispatch semantics after skills have started depending on them.

### Decision: Retry by failure class and idempotency

Add a stable failure taxonomy and retry policy. Retry timeout and transient failures only when the node/tool/action is idempotent and within limits. Do not retry non-idempotent side effects without a dedupe key. Graph-level provider retries must respect the provider adapter's retry budget and exhaustion metadata.

Rationale: Generic exception retry is unsafe for workflows with tools and side effects.

Alternative considered: Use a fixed retry count for all node failures. That can duplicate side effects and hide configuration errors.

### Decision: Keep repair backend-only and constrained

Stage 04 can support repair notes and allowed state patch/resume hooks for failed runs. The user-facing approval/edit experience remains Stage 05.

Rationale: Stage 04 needs reliability primitives, but building full HITL UI would broaden scope.

Alternative considered: Implement full resume UI now. That pulls Stage 05 forward and risks coupling UI to unfinished interrupt semantics.

## Risks / Trade-offs

- Checkpoint/projection drift -> Use checkpoint as authority, persist events transactionally where possible, and test rebuildable projections.
- Nested provider and graph retry loops -> Record provider attempts and only retry graph nodes when the classified failure remains retryable.
- Lock leakage after crash -> Use heartbeat and stale-lock takeover with audit metadata.
- Side-effect unknown status -> Stop and require repair instead of guessing.
- SQLite write contention -> Use WAL mode, short transactions, and one active executor per thread.
- Repair path can mutate unsafe state -> Restrict allowed repair fields and validate before resume.

## Migration Plan

1. Add storage path config, SQLite connection helper, and migrations.
2. Add repositories and tests for events, attempts, locks, side effects, provider attempts, projections, and repair notes.
3. Compile Stage 03 graph runtime with a SQLite checkpointer and preserve `thread_id` resume.
4. Persist events before SSE streaming and add replay cursor behavior.
5. Add state and replay/debug export endpoints.
6. Add locking, cancellation, retry/failure policy, provider attempts, and side-effect ledger.
7. Update shared schemas, frontend types, docs, and regression tests.

Rollback can disable reliability routing and fall back to Stage 03 process-local graph execution, but any existing SQLite database should be left intact for debug export.

## Open Questions

- Which exact local path should be the default database location: `~/.kira-agent/kira.db` or a platform-specific app data directory?
- Should Stage 04 expose `POST /api/runs/{thread_id}/resume` as a backend primitive now, or only implement internal resume tests and leave the public endpoint to Stage 05?
- How much repair state editing should be allowed before Stage 05 HITL UI exists?
