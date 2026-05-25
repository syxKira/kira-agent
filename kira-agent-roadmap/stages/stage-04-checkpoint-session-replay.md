# Stage 04: Reliable Graph Runtime + Replay

## Goal

Turn the Stage 03 graph runner into a reliable local workflow runtime: durable SQLite checkpointing, `thread_id` resume, session projection, debug replay, idempotency keys, bounded retries, per-run locks, side-effect tracking, and structured failure handling. A Kira run can stop, fail, resume, and be inspected without duplicating completed work.

## Why This Stage

LangGraph interrupt and replay require durable checkpointing, but checkpointing alone is not enough for a general web agent. Workflows will call tools, wait for humans, stream events, and sometimes perform external side effects through skill tools. Before Kira exposes HITL as a product experience, the graph runtime needs a clear reliability contract: deterministic replay where possible, idempotent side effects where necessary, and explicit recovery paths when something fails.

## Scope

- SQLite checkpointer for compiled graphs.
- `thread_id` as the stable run cursor.
- Session projection for UI state and replay.
- `GET /api/runs/{thread_id}/state`.
- Debug replay/export for checkpoints, events, tools, and audit summaries.
- Reliability contract for workflow nodes, tool calls, interrupts, and resumes.
- Per-`thread_id` run lock to prevent duplicate active executors.
- Monotonic event sequence for SSE, state projection, and replay.
- Idempotency keys and side-effect ledger for tool calls and external actions.
- Retry policy with timeout, backoff, max attempts, provider retry coordination, and non-retryable error classes.
- Cancellation and graceful shutdown behavior.
- Manual repair path for failed runs: inspect, edit allowed state, resume from checkpoint.
- Redacted provider/model attempt metadata in checkpoints, projections, and debug replay.

Excluded:

- Long-term memory semantics.
- Multi-turn conversation transcript and chat history context.
- Production multi-user storage.
- Cloud sync.
- Distributed worker queues.
- Exactly-once guarantees for remote systems that do not support idempotency keys.

## Inputs And Dependencies

- Stage 03 graph runtime.
- LangGraph SQLite checkpointer.
- Local SQLite database path policy.
- Stage 02 tool result normalization and audit hooks.
- Real LLM provider layer with provider timeout, retry, stream mapping, fixture fallback, and structured upstream errors.

## Design

The checkpointer is the durable graph state authority. Kira may maintain projection tables for fast UI reads, but projections are derived from checkpoint/event/audit records. Reusing a `thread_id` resumes the same graph execution lineage.

Kira follows the standard durable-execution guidance used by graph/workflow systems: persist progress at safe boundaries, keep nodes deterministic when possible, isolate non-deterministic or side-effecting work, and make resume operations idempotent. LangGraph's checkpointer provides durable state, but Kira owns the product-level reliability contract around side effects, user resumes, and UI-visible replay.

State projection contains:

- current run status;
- selected skill;
- latest workflow state summary;
- pending interrupt if present;
- tool result summaries;
- event replay cursor;
- audit references.
- selected provider profile ID, model name, and fallback status, with secrets redacted.

### Runtime Reliability Contract

| Area | Rule |
| --- | --- |
| State authority | Checkpointed graph state is authoritative; session tables are derived projections |
| Thread ownership | Only one active executor may run for a `thread_id`; duplicate start/resume returns current status or structured conflict |
| Node determinism | Nodes should be pure state transforms unless they call registered tools or explicit side-effect wrappers |
| Idempotency | Every tool call and side-effect action gets a stable idempotency key: `thread_id + checkpoint_id + node + call_index + tool` |
| Side effects | External effects are recorded in a ledger before/after execution so replay can reuse completed results |
| Retry | Retry only provider/tool/network/timeouts classified as retryable; never retry non-idempotent side effects without a dedupe key |
| Timeout | Node/tool timeouts are explicit, surfaced in state, and emitted as ordered events |
| Cancellation | Stop requests mark the run as cancelling, stop scheduling new work, and checkpoint a terminal/cancelled projection |
| Interrupt | Interrupt payloads are JSON-serializable, checkpointed, and resume values are validated before graph continuation |
| Replay | Replay re-emits stored events/projections; it does not re-run tools or side effects by default |

### Failure Taxonomy

Kira normalizes failures into stable classes so UI, tests, and recovery can behave consistently:

| Error Class | Examples | Default Recovery |
| --- | --- | --- |
| `validation_error` | invalid workflow manifest, bad tool args | fail fast, user/skill author fixes input |
| `permission_error` | denied Python run, forbidden file path | emit interrupt or fail with action guidance |
| `timeout_error` | provider/tool/node timeout | retry if safe, then fail with resume option |
| `transient_external_error` | temporary network/service issue | bounded retry with backoff |
| `provider_config_error` | missing default model, invalid baseURL, missing API key with no fixture fallback | fall back to fixture if policy allows, otherwise fail fast |
| `provider_stream_error` | malformed remote chunk, unexpected finish, invalid JSON frame | fail provider call, emit structured error, do not corrupt graph state |
| `tool_error` | tool returned structured failure | no retry unless tool marks it retryable |
| `side_effect_conflict` | duplicate external action, unknown remote status | require user repair or skill-specific reconciliation |
| `cancelled` | user stop or graceful shutdown | checkpoint cancelled state; allow explicit resume if workflow supports it |
| `invariant_error` | impossible state, missing checkpoint, event ordering bug | stop run and export debug bundle |

### Storage Additions

Beyond LangGraph checkpoints, Stage 04 introduces small local tables:

| Table | Purpose |
| --- | --- |
| `run_locks` | one active executor per `thread_id`, heartbeat, stale-lock takeover policy |
| `run_events` | normalized KiraEvents with monotonically increasing `seq` per run |
| `side_effect_ledger` | idempotency key, node, tool/action, args hash, status, result hash, audit ref |
| `run_attempts` | attempt number, start/end, durability mode, failure class |
| `provider_attempts` | provider profile ID, model, timeout, retry count, fallback flag, redacted error summary |
| `repair_notes` | optional user/developer repair notes for debug replay |

SQLite is still the local v0 store. Use WAL mode and short transactions for run locks and event writes.

### Durability Mode

Default local durability should favor correctness over raw speed:

- use synchronous checkpoint persistence for workflow steps that precede HITL or side effects;
- allow async persistence only for low-risk streaming/projection updates;
- record the chosen durability mode in `run_attempts` so replay explains what happened.

### Provider Retry Boundary

The real LLM provider adapter may retry transport-level failures within its configured `timeout` and `retry` policy. The graph runtime should not blindly retry a whole node after the provider adapter has exhausted its own retry budget unless the node is explicitly marked idempotent and the failure class remains retryable. This avoids double retry loops that make local debugging confusing and can duplicate downstream side effects after a model call.

## Implementation Tasks

1. Add SQLite storage path and migrations.
2. Compile graphs with a SQLite checkpointer.
3. Persist and reuse `thread_id`.
4. Implement state projection endpoint.
5. Add per-run lock acquisition, heartbeat, stale-lock handling, and duplicate resume protection.
6. Add KiraEvent persistence with per-run monotonic sequence numbers.
7. Add side-effect ledger and idempotency key helper for tool calls/external actions.
8. Add retry/timeout policy and failure taxonomy, including provider config and stream errors.
9. Persist redacted provider attempt metadata and fixture fallback status.
10. Add stop/cancel and graceful shutdown behavior.
11. Implement replay/export endpoint or debug command equivalent.
12. Add checkpoint resume tests.
13. Add corrupted/missing checkpoint error handling.
14. Add fault-injection tests for retry, duplicate resume, cancelled run, stale lock, provider timeout, provider stream error, and side-effect replay.

## Validation

- A test graph can pause or stop and resume with the same `thread_id`.
- State endpoint returns a stable projection.
- Replay reconstructs key events without re-running tools.
- Missing thread IDs return structured errors.
- Duplicate resume requests cannot create two active graph executors.
- A retryable tool failure is retried within limits and records attempts.
- Provider retry exhaustion is visible as a structured failure without leaking API keys.
- Fixture fallback status is preserved in state projection and replay.
- A completed side-effect tool result is reused on replay/resume instead of executed again.
- Event sequence numbers remain stable across SSE reconnect and replay.
- Cancelled and failed runs remain inspectable from state and debug export.

## Exit Criteria

- Checkpointed graph state is reliable enough for HITL and side-effecting skill workflows.
- Frontend can inspect run state without knowing LangGraph internals.
- Runtime failures are classified, audited, and recoverable or clearly terminal.
- Kira can explain whether a resume will re-run or reuse each completed step.

## Deferred Work

- User-facing HITL resume lands in Stage 05.
- Project knowledge retrieval lands in Stage 06.
- Memory records land in Stage 07.
- Conversation transcript and follow-up context lands in Stage 08.
- Production storage choices remain deferred.
- Distributed queues, remote workers, and multi-process exactly-once semantics remain deferred.
