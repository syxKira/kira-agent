# Appendix: Graph Runtime Reliability

## Purpose

Kira's graph runtime should be treated as a workflow engine, not just a function caller. LangGraph provides `StateGraph`, persistence, interrupts, and event streaming; Kira adds the product-level reliability contract needed for a local web agent: run ownership, idempotency, retry boundaries, side-effect accounting, replay semantics, and repair paths.

## Design Principles

| Principle | Meaning |
| --- | --- |
| Checkpoint is authority | Checkpointed state is the source of truth; UI/session tables are derived |
| One active executor | A `thread_id` can have only one active runner at a time |
| Deterministic by default | Nodes should be pure state transforms unless they call tools or explicit side-effect wrappers |
| Side effects are ledgered | Any external action must have an idempotency key and ledger record |
| Replay is read-only | Replay reconstructs state/events and does not re-run tools unless a user explicitly starts a new attempt |
| Retry is classified | Retry decisions are based on error class and idempotency, not generic exceptions |
| Human repair is first-class | Failed/interrupted runs can be inspected, patched within allowed fields, and resumed |

## Runtime Contract

### Thread And Run Ownership

- `thread_id` is the stable resume cursor and the unit of locking.
- `run_locks` stores `thread_id`, owner, heartbeat, and expiry.
- Duplicate `POST /resume` calls must not create duplicate graph runners.
- If a stale lock is detected, Kira records takeover metadata before resuming.

### Event Ordering

- Every persisted KiraEvent has a monotonically increasing `seq` per `thread_id`.
- SSE reconnect starts from a cursor and replays missed events before live events.
- State projection stores the latest emitted event sequence so UI and replay can converge.

### Idempotency Keys

Every side-effect-capable tool call receives a stable idempotency key:

```text
thread_id + checkpoint_id + node_name + call_index + tool_name + args_hash
```

The key is passed to tools that support dedupe. If a tool cannot support dedupe, its manifest must mark the action as non-idempotent and require HITL before retry or replay.

### Side-Effect Ledger

`side_effect_ledger` records:

- idempotency key;
- thread/checkpoint/node/tool;
- redacted args hash;
- status: `planned`, `started`, `completed`, `failed`, `unknown`;
- result hash and summary;
- external reference ID when available;
- audit record ID.

On resume, Kira checks the ledger before executing side effects. Completed entries reuse stored results. `unknown` entries require skill-specific reconciliation or user repair.

### Retry Policy

| Field | Default |
| --- | --- |
| max attempts | 2 for provider/transient tool calls; 0 for non-idempotent side effects |
| backoff | exponential with jitter |
| timeout | node/tool-specific, with a global cap |
| retryable | timeout, transient external errors, provider rate/connection errors |
| non-retryable | validation, permission, invariant, denied HITL, non-idempotent side effect |

Skill workflow manifests may narrow retry limits, but cannot expand beyond core safety policy.

Provider calls have an inner retry boundary. The OpenAI-compatible provider adapter owns configured remote retry for HTTP failures, rate/connection errors, malformed chunks, and timeout handling. The graph runtime records provider attempts and may retry the node only after the provider adapter returns a classified retryable failure and the node is still safe to repeat.

### Cancellation And Shutdown

- Stop requests set a cancellation flag and stop scheduling new graph work.
- In-flight tools should receive cancellation when possible; otherwise Kira waits until timeout.
- Graceful shutdown drains active runs to a checkpoint boundary when possible.
- Cancelled runs remain inspectable and may be resumed only if the workflow declares it can resume after cancellation.

## Error Taxonomy

| Error Class | Runtime Behavior |
| --- | --- |
| `validation_error` | fail fast; skill/input must be fixed |
| `permission_error` | emit interrupt if approval can resolve; otherwise fail |
| `timeout_error` | retry if idempotent and within limits |
| `transient_external_error` | retry with backoff |
| `provider_config_error` | fail fast or fixture fallback if policy allows |
| `provider_stream_error` | stop provider call, emit structured error, preserve checkpoint |
| `tool_error` | follow tool-provided retryability |
| `side_effect_conflict` | stop and require reconciliation |
| `cancelled` | checkpoint cancelled projection |
| `invariant_error` | stop, export debug bundle, do not auto-resume |

## API And UI Implications

- `GET /api/runs/{thread_id}/state` includes run status, lock status, latest event seq, retry attempts, failed node, pending interrupt, and side-effect summaries.
- Replay/debug export includes checkpoints, normalized events, ledger entries, tool summaries, audit IDs, and repair notes.
- Frontend timeline should show retries, reused side effects, stale locks, cancellation, and repairable failures as explicit events.

## Test Matrix

| Case | Expected Result |
| --- | --- |
| process stops after checkpoint | same `thread_id` resumes from last checkpoint |
| duplicate resume requests | only one active executor; loser gets current status/conflict |
| retryable tool timeout | bounded retry, attempt events, final success/failure |
| provider timeout/retry exhaustion | structured provider error, no API key leakage |
| no provider key with fallback enabled | fixture fallback recorded in state/replay |
| completed side effect then replay | stored result is reused; external action is not repeated |
| unknown side-effect status | run pauses for repair/reconciliation |
| SSE reconnect | missed events replay in sequence, then live stream continues |
| corrupted checkpoint | structured invariant error and debug export |
| user cancellation | run reaches cancelled projection and remains inspectable |

## Deferred

- Distributed worker queues.
- Multi-process exactly-once execution.
- Remote durable stores beyond SQLite.
- Skill-specific reconciliation plugins for external systems.
