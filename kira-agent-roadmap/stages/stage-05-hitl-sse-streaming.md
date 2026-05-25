# Stage 05: HITL + SSE Streaming

## Goal

Connect LangGraph `interrupt` and `astream_events` to the FastAPI SSE and frontend resume flow. Users can approve, reject, or edit a graph decision and resume the same `thread_id`.

## Why This Stage

Human-in-the-loop is a core Kira boundary: approvals, edits, questions, and risky Python script decisions should be protocol events, not frontend-only state.

## Scope

- `interrupt` payload convention.
- `POST /api/runs/{thread_id}/resume`.
- SSE mapping for token, tool, checkpoint, retry, side-effect reuse, interrupt, resume, done, and error events.
- Cursor-based SSE reconnect using Stage 04 monotonic event sequence.
- Preservation of real provider stream semantics: visible chunks, hidden thinking chunks, done, and structured upstream errors.
- Timeline rendering for graph/tool events, including running status rows and expandable tool cards.
- Frontend HITL panel for approval/edit/question responses.
- Resume tests using the same thread ID.

Excluded:

- Complex multi-reviewer workflows.
- Persistent notification systems.
- Remote auth.

## Inputs And Dependencies

- Stage 04 reliable graph runtime: checkpointer, run lock, event sequence, side-effect ledger, and retry/error taxonomy.
- Real LLM provider stream mapping from remote chunks to KiraEvents.
- LangGraph `interrupt` and `Command(resume=...)`.
- LangGraph `astream_events`.
- Frontend event stream from Stage 01.

## Design

Interrupt payloads must be JSON-serializable and small:

```python
class InterruptPayload(TypedDict):
    kind: Literal["approval", "edit", "question", "python_approval"]
    title: str
    body: str
    data: dict
```

Frontend renders the payload as an inline timeline break plus a focused side/bottom panel, then posts a resume value. Backend resumes by invoking the same graph with `Command(resume=...)` and the same `thread_id`. Resume must acquire the Stage 04 run lock before graph execution; duplicate resume attempts return current run status or a structured conflict instead of starting another executor.

The event mapper converts LangGraph event names into KiraEvent types so the frontend does not depend on LangGraph internals. Every persisted event includes a per-run `seq`; SSE reconnect can replay from the last seen sequence before joining the live stream.

Provider stream mapping is already owned by the focused real LLM provider change. Stage 05 must not re-parse provider-specific chunks in the frontend. It only streams normalized KiraEvents and preserves the hidden-thinking boundary: `thinking_delta` can appear as status/debug metadata but never as normal assistant answer text.

Timeline event mapping:

| KiraEvent | UI block |
| --- | --- |
| `text_delta` | Assistant text block, streamed inline |
| `thinking_delta` | Collapsed status/debug row, not answer text |
| `tool_start` | Status row plus collapsed tool card shell |
| `tool_result` | Tool card result preview with copy and expand controls |
| `retry` | Small status row with attempt number and retry reason |
| `side_effect_reused` | Debug-visible marker that a completed side effect was not re-executed |
| `checkpoint` | Small timeline marker, hidden by default outside debug mode |
| `interrupt` | Waiting-for-user row and HITL panel |
| `resume` | User decision marker |
| `done` | Completed row and idle composer |
| `error` | Error row with retry/resume affordance when available |

## Implementation Tasks

1. Define interrupt payload schema.
2. Add resume endpoint.
3. Implement `astream_events` to SSE mapper.
4. Add SSE cursor/reconnect support using event `seq`.
5. Add timeline renderer for provider text/thinking, tool/status/retry/checkpoint/interrupt events.
6. Add frontend HITL panel.
7. Wire `ask_user_question` to interrupt.
8. Wire risky Python approval to interrupt.
9. Add fixture graph with approval and edit interrupts.
10. Add resume-order, reconnect, and duplicate-resume tests.

## Validation

- SSE streams token/tool/checkpoint/interrupt events in order.
- SSE reconnect replays missed events in sequence without duplicates.
- Provider `thinking_delta` remains hidden from normal assistant answer rendering after graph and SSE mapping.
- Provider upstream failures render as structured `error` events with retry/resume affordances where appropriate.
- Tool calls render as timeline cards without exposing raw unbounded payloads by default.
- Frontend can approve an interrupt and continue the run.
- Rejected approval returns a structured tool/workflow result.
- Resume uses the same `thread_id`.
- Duplicate resume cannot create two active executors.

## Exit Criteria

- Human decisions are durable graph state transitions.
- Frontend can complete at least one approval and one question flow.

## Deferred Work

- Detailed permission policy and remembered approvals land in Stage 09.
- Rich skill-specific HITL forms are deferred.
