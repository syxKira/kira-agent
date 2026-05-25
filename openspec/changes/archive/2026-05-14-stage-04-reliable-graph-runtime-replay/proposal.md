## Why

Stage 03 proved that skill-defined LangGraph workflows can run, but graph execution is still process-local and cannot resume, replay, or protect side effects. Stage 04 adds the reliability layer needed before user-facing HITL and side-effecting skill workflows: durable checkpointing, stable run state, event replay, idempotency, locks, cancellation, retry classification, and inspectable failures.

## What Changes

- Add local SQLite-backed runtime storage for checkpoints, run events, projections, locks, attempts, provider attempts, side-effect ledger records, and repair notes.
- Compile graph runs with a SQLite checkpointer and use `thread_id` as the stable resume cursor.
- Add `GET /api/runs/{thread_id}/state` for frontend-safe session projection.
- Add replay/debug export for stored events, checkpoint summaries, tool summaries, side-effect ledger summaries, provider attempt summaries, and repair notes.
- Add per-run lock acquisition, heartbeat, stale-lock handling, duplicate executor protection, cancellation, and graceful shutdown behavior.
- Add monotonic persisted Kira event sequencing with SSE reconnect/replay support.
- Add side-effect idempotency keys and a ledger for graph tool calls and future external actions.
- Add retry/timeout policy and a normalized failure taxonomy across graph nodes, tools, provider calls, cancellation, and invariants.
- Persist selected provider/model attempt metadata and fixture fallback status in redacted form.
- Allow failed runs to remain inspectable and provide a constrained manual repair/resume path for allowed state fields.

## Scope

- Backend-focused reliability work in `server/`, with shared contract updates in `src/` and frontend TypeScript updates where new state/replay/event payloads are exposed.
- SQLite remains the local v0 storage backend.
- Reliability wraps the Stage 03 graph runtime; direct fixture/provider runs should remain available and inspectable where practical.
- The implementation must preserve Stage 02 file/Python tool safety and real provider redaction.

## Non-goals

- No full HITL approval/edit UI; Stage 05 owns user-facing interrupt/resume panels.
- No project knowledge retrieval index, cited retrieval, or ContextItem injection; Stage 06 owns that.
- No memory records or memory extraction; Stage 07 owns that.
- No production multi-user storage, cloud sync, distributed workers, remote queue, or exactly-once guarantees for remote systems without idempotency support.
- No write/edit/delete/patch/stage project tools and no general shell tool.
- No built-in business workflow in Kira core.

## Capabilities

### New Capabilities

- `durable-run-storage`: SQLite storage, migrations, checkpoint integration, run events, run attempts, provider attempts, projections, and repair notes.
- `run-state-replay`: State projection, event replay, debug export, missing/corrupted checkpoint handling, and inspectable terminal runs.
- `run-locking-cancellation`: Per-`thread_id` executor locks, heartbeat, stale-lock takeover, duplicate resume protection, stop/cancel, and graceful shutdown.
- `side-effect-idempotency-ledger`: Idempotency key generation, side-effect ledger lifecycle, completed result reuse, and unknown-status repair handling.
- `retry-failure-policy`: Failure taxonomy, retryability rules, timeout/backoff policy, provider retry coordination, and structured failure metadata.

### Modified Capabilities

- `langgraph-runtime-execution`: Replace Stage 03 process-local/non-durable execution with checkpointed graph execution, stable `thread_id` resume, and reliability metadata enforcement.
- `graph-event-streaming`: Persist event sequences, support replay/reconnect, and add reliability event payloads for retry, checkpoint, cancellation, and side-effect reuse.
- `toolnode-tool-dispatch`: Add idempotency and side-effect ledger requirements around graph tool calls.
- `llm-provider-selection`: Persist redacted provider attempt metadata and coordinate provider retry exhaustion with graph retry policy.

## Impact

- Adds local SQLite storage modules and migration tests under `server/`.
- Extends graph runtime execution, run API, SSE streaming, run records, and app lifecycle.
- Adds new API surface such as `GET /api/runs/{thread_id}/state`, stop/cancel, resume hooks sufficient for reliability, and replay/debug export.
- Adds shared schemas for run state projection, replay/debug export, retry/failure events, and side-effect ledger summaries.
- Adds tests for checkpoint resume, event replay, duplicate resume, stale locks, cancellation, retryable failures, provider retry exhaustion, side-effect reuse, and secret redaction.

## Acceptance Criteria

- A test skill graph can pause, stop, fail, and resume with the same `thread_id`.
- `GET /api/runs/{thread_id}/state` returns a stable projection with status, latest event sequence, selected skill, provider/model metadata, lock status, attempts, tool summaries, side-effect summaries, and pending interrupt when present.
- SSE reconnect or replay returns persisted events in stable sequence without re-running tools.
- Duplicate start/resume for the same active `thread_id` cannot create two executors.
- Retryable provider/tool/node failures retry within limits and record attempts; non-retryable failures remain inspectable.
- Provider retry exhaustion and fixture fallback are visible in redacted state/replay metadata without leaking API keys.
- Completed side-effect ledger entries are reused on resume/replay; unknown side-effect status requires repair or reconciliation.
- Cancelled and failed runs remain inspectable through state and debug export.

## Risks

- Checkpointer and Kira projection tables can diverge if writes are not ordered carefully; checkpoint remains authoritative and projections must be derivable.
- Retry policy can duplicate work if idempotency keys are unstable; side-effecting tool calls must be ledgered before execution.
- Event replay can conflict with live SSE if locks and cursors are loose; per-run monotonic sequence and cursor handling must be tested.
- Provider and graph retries can create nested retry loops; graph retry must respect provider adapter retry exhaustion metadata.
- Repair/resume can become a full HITL product; Stage 04 should provide backend reliability hooks while deferring UI-heavy approval flows to Stage 05.
