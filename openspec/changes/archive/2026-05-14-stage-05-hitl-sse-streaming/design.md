## Context

Kira already has a local FastAPI backend, Vite React workbench, shared schemas, provider fixture/real streaming, LangChain Core tools, skill-loaded LangGraph workflows, and Stage 04 durable runtime foundations. Stage 04 introduced persisted events, run locks, side-effect ledger behavior, replay/state APIs, and checkpoint-oriented resume foundations, but it did not turn LangGraph `interrupt` into a complete local human-in-the-loop flow.

Stage 05 builds the next boundary: graph execution can pause for human approval, edit, or question input, stream that interruption to the frontend over normalized SSE, accept a resume value, and continue the same `thread_id`. This stage must keep provider output normalized and redacted, keep hidden thinking out of visible answer text, and avoid Stage 06+ project knowledge, memory, packaging, and policy work.

## Goals / Non-Goals

**Goals:**

- Define a small JSON-serializable interrupt payload contract for approval, edit, question, and Python approval flows.
- Persist and stream `interrupt` and `resume` Kira events with monotonic sequence numbers before frontend delivery.
- Resume checkpointed skill graph runs through LangGraph `Command(resume=...)` while using Stage 04 run locks and idempotency guards.
- Map LangGraph `astream_events` into Kira event types without exposing raw LangGraph/provider internals to the frontend.
- Add frontend timeline blocks and a focused HITL panel that can approve, reject, edit, answer, or cancel the active prompt.
- Provide deterministic fixture skills for approval and edit/question flows so tests do not require a real API key.

**Non-Goals:**

- No Stage 06 project knowledge retrieval or expanded skill package contract.
- No Stage 07 memory storage, extraction, or memory inspector.
- No Stage 08 policy engine, remembered approvals, audit UI, packaging, remote auth, or notification system.
- No general shell tool and no project-file mutation tools.
- No multi-reviewer or asynchronous out-of-app approval workflow.

## Decisions

### Decision: Normalize interrupts into Kira events, not frontend-specific state

LangGraph interrupts SHALL become persisted `KiraEvent(type="interrupt")` payloads with a compact `interrupt_id`, `kind`, `title`, `body`, `data`, `allowed_responses`, and redacted metadata. The frontend renders these events, but backend storage remains the source of truth.

Alternatives considered:

- Frontend-only modal state: rejected because reconnect/replay would lose the pending decision.
- Raw LangGraph interrupt payload passthrough: rejected because it exposes runtime internals and makes frontend compatibility depend on LangGraph payload shape.

### Decision: Resume through the existing run lifecycle

`POST /api/runs/{thread_id}/resume` SHALL validate the resume value, acquire the Stage 04 run lock, persist a `resume` event, and continue the graph with the same `thread_id`. Duplicate active resumes SHALL return a structured conflict or current state rather than spawning another executor.

Alternatives considered:

- Create a new run for each resume: rejected because it breaks checkpoint and side-effect ledger identity.
- Let the browser resume directly over SSE: rejected because request validation, lock acquisition, and persistence belong in the backend.

### Decision: Keep event mapping provider-neutral

The backend SHALL own mapping from LangGraph `astream_events` and provider events into Kira events. The frontend SHALL render normalized event types and must not parse provider chunks, LangGraph callback names, or raw tool traces.

Alternatives considered:

- Teach frontend about LangGraph event names: rejected because it couples UI to runtime internals.
- Collapse all graph status into `thinking_delta`: rejected because HITL, tool lifecycle, retry, checkpoint, and side-effect reuse need distinct timeline behavior.

### Decision: Use fixture HITL skills for deterministic coverage

Stage 05 SHALL include at least one built-in or test fixture skill that emits approval and edit/question interrupts. It can use deterministic nodes and fixture provider behavior so tests run without real credentials.

Alternatives considered:

- Test only with a real model producing interrupts: rejected because default tests must not require network or API keys.
- Hardcode core workflow nodes for HITL demos: rejected because concrete workflows belong to skills.

### Decision: Keep resume validation generic

The interrupt payload SHALL declare generic response constraints such as approval decision, optional edited text, question answer text, and optional rejection reason. Rich skill-specific forms are deferred; Stage 05 validates only the shared payload envelope and response kind.

Alternatives considered:

- Build arbitrary JSON Schema form rendering now: rejected as Stage 06/08 complexity.
- Accept any resume blob: rejected because malformed resume values can corrupt checkpointed graph state.

## Risks / Trade-offs

- Raw runtime payload leakage -> The event mapper will whitelist public fields and reuse provider redaction helpers before persistence and SSE.
- Duplicate resume races -> Resume uses persistent run locks and returns structured conflict/state when another executor is active.
- Reconnect confusion around pending interrupts -> The stream replays persisted events by `after_seq`; state projection includes the current pending interrupt.
- Skill-specific HITL needs may outgrow the generic panel -> Stage 05 supports only approval/edit/question shapes and leaves rich forms for later stages.
- Provider token streaming may interleave with graph events -> The mapper preserves event order by persisting each normalized event before SSE emission.

## Migration Plan

1. Add shared schemas and TypeScript types for interrupt payloads, resume requests, resume responses, and expanded reliability event payloads.
2. Extend graph runtime event mapping to consume `astream_events`, emit normalized Kira events, and persist them through Stage 04 storage.
3. Implement resume endpoint behavior using the existing run lock, checkpoint, and replay foundations.
4. Replace placeholder-only `ask_user_question` graph behavior with interrupt-producing behavior while preserving structured validation errors.
5. Add HITL fixture skills and backend tests for approval, rejection, edit/question, reconnect, duplicate resume, and redaction.
6. Add frontend HITL panel and timeline rendering tests.

Rollback is straightforward during local development: remove the Stage 05 change or disable HITL fixture skill selection. Existing direct fixture/provider runs must continue to pass without calling the resume path.

## Open Questions

- Whether approval/edit/question resume payloads should expose stable `decision_id` in addition to `interrupt_id` for future audit UI.
- Whether risky Python approval should initially be a separate interrupt kind or an approval interrupt with `data.tool_name = "run_python_script"`.
- Whether pending interrupt state should be shown in the right inspector in Stage 05 or only in the timeline and focused panel.
