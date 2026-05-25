## 1. Storage Foundation

- [x] 1.1 Add SQLite runtime storage configuration with default user-local path and test override.
- [x] 1.2 Create `server/src/kira_server/storage/` for connection management, migrations, repositories, and test helpers.
- [x] 1.3 Implement idempotent migrations for run events, run attempts, provider attempts, run locks, side-effect ledger, projections, repair notes, and checkpointer tables.
- [x] 1.4 Configure SQLite WAL mode and short transaction helpers.
- [x] 1.5 Add storage tests for fresh initialization, repeated migrations, test path override, and no project-root runtime database writes.

## 2. Checkpointed Graph Execution

- [x] 2.1 Add LangGraph SQLite checkpointer dependency or adapter required by the installed LangGraph version.
- [x] 2.2 Compile Stage 03 workflows with a SQLite-backed checkpointer for Stage 04 graph runs.
- [x] 2.3 Use `thread_id` as the stable graph checkpoint/resume cursor.
- [x] 2.4 Persist run attempts with start/end time, status, durability mode, selected skill, selected model, and failure class.
- [x] 2.5 Preserve direct provider/fixture runs while routing skill graph runs through checkpointed execution.
- [x] 2.6 Add tests for checkpoint write, same-thread resume, new-thread creation, and process-local fallback avoidance.

## 3. Persisted Events And SSE Replay

- [x] 3.1 Implement a run event repository with monotonic per-`thread_id` sequence allocation.
- [x] 3.2 Persist graph events before streaming them over SSE.
- [x] 3.3 Add SSE reconnect cursor support to replay persisted events after a provided sequence.
- [x] 3.4 Add replay API or debug export path that returns persisted events without re-running graph work.
- [x] 3.5 Add tests for stable event sequence after restart, replay order, reconnect missed-event replay, and no tool/provider execution during replay.

## 4. State Projection And Debug Export

- [x] 4.1 Add `GET /api/runs/{thread_id}/state` returning frontend-safe state projection.
- [x] 4.2 Include status, selected skill, workflow summary, latest event sequence, provider/model metadata, fixture fallback, attempts, lock status, tool summaries, side-effect summaries, pending interrupt when present, and repair status.
- [x] 4.3 Add debug export including checkpoint summary, persisted events, provider attempts, tool summaries, side-effect ledger summaries, audit references, and repair notes.
- [x] 4.4 Handle unknown `thread_id`, missing checkpoint, and corrupted checkpoint as structured errors.
- [x] 4.5 Add tests for state projection, not-found state, replay/export redaction, missing checkpoint, and corrupted checkpoint handling.

## 5. Run Locks And Cancellation

- [x] 5.1 Implement persistent run lock acquisition, heartbeat, release, expiry, and owner metadata.
- [x] 5.2 Reject duplicate active executors for the same `thread_id` with current state or structured conflict.
- [x] 5.3 Implement stale-lock takeover after expiry with takeover metadata.
- [x] 5.4 Add stop/cancel behavior that marks runs cancelling/cancelled and stops scheduling new graph nodes.
- [x] 5.5 Add graceful shutdown handling that avoids new graph work and checkpoints or marks active runs.
- [x] 5.6 Add tests for lock acquire/release, duplicate resume conflict, stale takeover, cancellation, cancelled state inspection, and graceful shutdown behavior.

## 6. Side-Effect Idempotency Ledger

- [x] 6.1 Implement idempotency key helper using thread ID, checkpoint ID, node name, call index, tool/action name, and args hash.
- [x] 6.2 Implement side-effect ledger repository with planned, started, completed, failed, and unknown statuses.
- [x] 6.3 Wrap graph ToolNode dispatch so side-effect-capable calls create ledger records before execution.
- [x] 6.4 Reuse completed ledger results on resume/replay instead of re-running side-effect-capable actions.
- [x] 6.5 Block automatic resume for unknown ledger status and require repair/reconciliation metadata.
- [x] 6.6 Add tests for stable keys, args-hash changes, ledger transitions, completed result reuse, unknown-status repair requirement, and non-idempotent no-auto-retry behavior.

## 7. Retry, Timeout, And Failure Policy

- [x] 7.1 Define failure taxonomy constants and structured failure payloads.
- [x] 7.2 Implement retry policy using failure class, node metadata, retry hints, timeout hints, idempotency, and global caps.
- [x] 7.3 Emit and persist retry attempt events or payloads.
- [x] 7.4 Enforce node/tool timeouts and mark timeout failures in state projection.
- [x] 7.5 Coordinate graph-level provider retry with provider adapter retry exhaustion metadata.
- [x] 7.6 Add tests for retryable timeout success, retry exhaustion, validation no-retry, permission no-retry, provider retry exhaustion, and redacted failure metadata.

## 8. Provider Attempt Persistence

- [x] 8.1 Persist provider attempts with provider profile ID/name, model, timeout, retry count, fallback flag, status, and redacted error summary.
- [x] 8.2 Record fixture fallback reason in provider attempt and state projection.
- [x] 8.3 Ensure provider attempts never store raw API keys or raw provider config objects.
- [x] 8.4 Add tests for real provider attempt persistence, fixture fallback attempt persistence, provider stream error classification, retry count visibility, and secret redaction.

## 9. Repair And Resume Hooks

- [x] 9.1 Add backend resume foundation for checkpointed graph runs without building Stage 05 HITL UI.
- [x] 9.2 Add repair note storage and replay/export inclusion.
- [x] 9.3 Add constrained repair-state validation for explicitly allowed fields only.
- [x] 9.4 Reject unsafe repair edits to provider secrets, event history, ledger records, and arbitrary workflow internals.
- [x] 9.5 Add tests for repair notes, allowed repair, unsafe repair rejection, terminal-state resume rejection, and repair-required side-effect status.

## 10. Shared Contracts, Frontend Types, And Docs

- [x] 10.1 Add shared schemas for run state projection, replay/debug export, failure metadata, retry events, and side-effect ledger summaries.
- [x] 10.2 Update TypeScript types for run state, replay/export, reliability event payloads, and lock/cancellation status.
- [x] 10.3 Keep the frontend workbench compatible with Stage 03 event rendering while tolerating reliability payloads.
- [x] 10.4 Update README/server docs with Stage 04 scope, APIs, storage path, and explicit Stage 05+ non-goals.
- [x] 10.5 Add frontend tests only where touched contracts or rendering behavior changes.

## 11. Security And Regression Tests

- [x] 11.1 Add tests proving raw API keys do not appear in checkpoints, projections, provider attempts, replay/export, repair notes, logs/diagnostics helpers, or frontend payloads.
- [x] 11.2 Add tests proving project file tools remain read-only through checkpointed ToolNode dispatch.
- [x] 11.3 Add tests proving replay is read-only and does not re-run tools, providers, or side effects.
- [x] 11.4 Add regression tests for Stage 01 direct fixture streams, Stage 02 tool metadata, Stage 03 skill graph execution, and real provider fallback.

## 12. Validation

- [x] 12.1 Run backend tests for storage, graph runtime, provider, tools, skills, locking, replay, retry, and repair.
- [x] 12.2 Run frontend tests/typecheck if TypeScript or rendering contracts are touched.
- [x] 12.3 Run `openspec validate "stage-04-reliable-graph-runtime-replay" --strict`.
- [x] 12.4 Run `openspec status --change "stage-04-reliable-graph-runtime-replay"` and confirm all artifacts are complete.
- [x] 12.5 Record verification commands and results in the implementation summary.
