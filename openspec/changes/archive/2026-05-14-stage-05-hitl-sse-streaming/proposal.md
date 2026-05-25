## Why

Stage 04 made graph runs durable and replayable, but human decisions are still only placeholders. Stage 05 turns LangGraph interrupts, resume values, and graph event streaming into first-class Kira events so the local web loop can pause for approval/edit/question input and continue the same `thread_id`.

## What Changes

- Add a typed HITL interrupt payload convention for approval, edit, question, and risky Python approval decisions.
- Implement resume semantics for interrupted graph runs using the existing Stage 04 run lock, checkpoint, event sequence, and side-effect ledger foundations.
- Map LangGraph `astream_events` into normalized Kira SSE events for tokens, thinking/status, tools, checkpoints, retries, side-effect reuse, interrupts, resumes, done, and errors.
- Extend SSE reconnect behavior so clients can replay persisted events by sequence before joining live execution.
- Add frontend timeline rendering for running graph/tool/status events and a focused HITL panel for approval, edit, and question responses.
- Add fixture skills/graphs that exercise approval and edit/question interrupts without requiring a real API key.
- Preserve provider stream boundaries: hidden thinking remains `thinking_delta` and is never merged into visible assistant text.
- Keep Stage 05 focused on local HITL/SSE behavior; do not add Stage 06 project knowledge retrieval, Stage 07 memory, or Stage 08 safety polish.

## Capabilities

### New Capabilities

- `hitl-interrupt-resume`: Defines durable interrupt payloads, resume request/response behavior, decision validation, and same-thread continuation.
- `timeline-hitl-ui`: Defines frontend timeline and HITL panel behavior for interrupt, resume, tool/status, retry, checkpoint, and side-effect reuse events.

### Modified Capabilities

- `hitl-question-placeholder`: Replaces the placeholder question tool behavior with graph interrupt-based question/resume behavior.
- `graph-event-streaming`: Expands event mapping from graph execution to include LangGraph `astream_events`, interrupt/resume, tool lifecycle, retry, checkpoint, and side-effect reuse events.
- `langgraph-runtime-execution`: Adds interrupt and `Command(resume=...)` execution requirements on top of Stage 04 durable graph runs.
- `local-run-api`: Adds concrete resume request handling and reconnect cursor behavior for run event streams.
- `local-web-workbench`: Adds HITL panel/timeline rendering requirements while keeping Stage 01/03 event rendering compatible.

## Impact

- Backend: `server/` FastAPI run routes, graph runtime execution, ToolNode dispatch event mapping, controlled Python approval integration, skill fixtures, and storage-backed event/replay handling.
- Frontend: `web/` run API client, event types, timeline rendering, running state controls, and HITL panel components.
- Shared contracts: `src/` schemas for interrupt payloads, resume requests/results, and expanded Kira event payloads.
- Tests: backend graph/resume/SSE reconnect tests, provider boundary regression tests, frontend HITL/timeline tests, and fixture runs that do not require real provider credentials.
- Dependencies: no new agent frameworks; continue using FastAPI, Vite React, LangGraph `interrupt`/`astream_events`, LangChain Core tool primitives, and the Stage 04 SQLite runtime storage.

## Scope

- Local FastAPI + Vite React HITL flow only.
- Same-thread resume for checkpointed skill graph runs.
- Durable event persistence before SSE emission.
- Deterministic fixture coverage for approval, rejection, edit, question, reconnect, duplicate resume, and provider stream boundary regressions.

## Non-goals

- No Stage 06 skill package contract expansion or project knowledge retrieval.
- No Stage 07 memory system.
- No Stage 08 remembered permissions, detailed policy engine, audit UI, packaging polish, or remote auth.
- No general shell tool and no new project-file write/edit/delete tools.
- No multi-reviewer or notification workflow.

## Acceptance Criteria

- A fixture skill emits an interrupt, the frontend renders a focused HITL panel, and submitting approval resumes the same `thread_id` to completion.
- Edit and question interrupts validate resume values and persist a visible resume decision marker.
- Rejecting an approval produces a structured workflow/tool result without duplicating prior completed side effects.
- SSE reconnect with `after_seq` replays missed events in order without duplicates or graph re-execution.
- Duplicate resume attempts cannot start two active executors for the same `thread_id`.
- Hidden provider thinking remains out of normal assistant answer rendering across graph streaming and replay.

## Risks

- LangGraph event payloads are more detailed than Kira should expose; the mapper must normalize and redact rather than leaking raw internals.
- Resume value validation can become skill-specific too early; Stage 05 should keep a small generic contract and defer rich forms.
- Duplicate resume and client reconnect races can create confusing UI states unless lock conflicts and persisted event replay are deterministic.
