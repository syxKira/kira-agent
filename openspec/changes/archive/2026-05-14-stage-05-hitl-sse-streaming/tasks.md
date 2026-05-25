## 1. Shared Contracts

- [x] 1.1 Add shared JSON schema for interrupt payloads with approval, edit, question, and python_approval kinds.
- [x] 1.2 Add shared JSON schema for resume requests and resume results.
- [x] 1.3 Expand the Kira event schema to include `tool_start`, `tool_result`, `retry`, `side_effect_reused`, `checkpoint`, `interrupt`, and `resume`.
- [x] 1.4 Add failure/redaction fields required by interrupt, resume, and graph event payloads without permitting raw provider secrets.
- [x] 1.5 Update TypeScript types for Stage 05 event payloads, interrupt payloads, resume requests, resume results, and pending HITL state.
- [x] 1.6 Add schema/type tests or validation fixtures for valid approval/edit/question interrupts and invalid payloads.

## 2. Backend HITL Models And Validation

- [x] 2.1 Add backend dataclasses or Pydantic models for interrupt payloads, allowed responses, resume values, and resume validation errors.
- [x] 2.2 Implement interrupt payload validation for required fields, supported kind, bounded title/body/data, and redaction.
- [x] 2.3 Implement resume value validation for approval approve/reject decisions.
- [x] 2.4 Implement resume value validation for edit replacement text with bounded content.
- [x] 2.5 Implement resume value validation for question answers and declared response fields.
- [x] 2.6 Implement resume value validation for python_approval decisions without adding a new general shell tool.
- [x] 2.7 Add backend unit tests for valid and invalid interrupt/resume payloads.

## 3. LangGraph Runtime Streaming

- [x] 3.1 Add a graph event mapper that converts LangGraph `astream_events` records into normalized Kira events.
- [x] 3.2 Map graph token/provider visible content to `text_delta` and hidden thinking/status content to `thinking_delta`.
- [x] 3.3 Map tool lifecycle events to `tool_start` and `tool_result` with bounded public payloads.
- [x] 3.4 Map checkpoint, retry, side-effect reuse, interrupt, resume, done, and error events to distinct Kira event types.
- [x] 3.5 Persist each normalized event before emitting it to SSE.
- [x] 3.6 Tolerate unknown LangGraph event names by ignoring them or emitting redacted debug/status events.
- [x] 3.7 Add backend tests for event ordering, one terminal event, unknown event tolerance, and hidden thinking separation.

## 4. Interrupt And Resume Execution

- [x] 4.1 Wire LangGraph `interrupt` into skill graph execution so valid interrupt payloads pause the run.
- [x] 4.2 Implement resume execution using LangGraph `Command(resume=...)` and the same `thread_id`.
- [x] 4.3 Persist `interrupt` and `resume` events in sequence order around the paused graph continuation.
- [x] 4.4 Reuse Stage 04 run locks during resume and return structured conflict/current state for duplicate resume attempts.
- [x] 4.5 Preserve Stage 04 side-effect ledger behavior across resume, including completed-result reuse.
- [x] 4.6 Block automatic resume when an unknown side-effect ledger state requires repair.
- [x] 4.7 Add backend tests for same-thread resume, duplicate resume conflict, terminal resume rejection, side-effect reuse, and repair-required blocking.

## 5. Local Run API And SSE Reconnect

- [x] 5.1 Implement `POST /api/runs/{thread_id}/resume` request/response handling.
- [x] 5.2 Return not-found, no-pending-interrupt, stale-interrupt, validation, and lock-conflict errors in structured API form.
- [x] 5.3 Include resume URL or resume-ready metadata in run creation/state payloads for skill graph runs.
- [x] 5.4 Include pending interrupt summaries in `GET /api/runs/{thread_id}/state`.
- [x] 5.5 Ensure `GET /api/runs/{thread_id}/replay` includes interrupt and resume markers without re-running work.
- [x] 5.6 Extend `GET /api/runs/{thread_id}/events?after_seq=` tests for reconnect after interrupt/resume.
- [x] 5.7 Add tests proving reconnect replay does not call providers, tools, side effects, or new graph nodes.

## 6. Tool And Skill HITL Integration

- [x] 6.1 Replace graph-context `ask_user_question` placeholder behavior with a question interrupt flow.
- [x] 6.2 Preserve structured non-interactive fallback for `ask_user_question` outside interrupt-capable graph execution.
- [x] 6.3 Add a deterministic fixture skill that pauses for approval and completes after approve.
- [x] 6.4 Add deterministic fixture paths for rejection, edit, and question resume values.
- [x] 6.5 Wire risky controlled Python execution approval to python_approval interrupts where Stage 02/04 metadata marks approval as required.
- [x] 6.6 Add tests for `ask_user_question` validation, question resume, approval rejection, edit resume, and python_approval approval/denial.

## 7. Frontend API And State

- [x] 7.1 Add frontend API helpers for `POST /api/runs/{thread_id}/resume`.
- [x] 7.2 Track pending interrupt state from event stream and state/replay payloads.
- [x] 7.3 Track last seen event sequence and use it for reconnect cursor behavior.
- [x] 7.4 Keep direct fixture/provider runs compatible when no HITL event is present.
- [x] 7.5 Add frontend unit tests for resume API payload construction and error handling.

## 8. Timeline And HITL UI

- [x] 8.1 Render `tool_start`, `tool_result`, `retry`, `checkpoint`, `side_effect_reused`, `interrupt`, and `resume` event blocks.
- [x] 8.2 Add a focused HITL panel for approval interrupts with approve/reject actions.
- [x] 8.3 Add edit interrupt UI with initialized editable content and bounded submission.
- [x] 8.4 Add question interrupt UI with declared response fields and validation feedback.
- [x] 8.5 Add python_approval UI that clearly shows the bounded script approval request without exposing raw internals.
- [x] 8.6 Disable or replace composer while waiting for HITL input and restore it after done/error/cancel.
- [x] 8.7 Ensure hidden thinking is never rendered as normal assistant answer text across HITL timelines.
- [x] 8.8 Add frontend rendering tests for approval, rejection, edit, question, retry, checkpoint, side-effect reuse, and reconnect replay.

## 9. Security, Redaction, And Regression Coverage

- [x] 9.1 Add tests proving raw API keys do not appear in interrupts, resume events, replay/export, state projection, logs/diagnostics helpers, or frontend DOM.
- [x] 9.2 Add tests proving raw LangGraph event payloads and raw provider config objects are not sent to the frontend.
- [x] 9.3 Add regression tests for Stage 01 fixture streams, Stage 03 graph tool results, Stage 04 replay/state APIs, and real provider fixture fallback.
- [x] 9.4 Add tests proving project file tools remain read-only through interrupted/resumed ToolNode execution.
- [x] 9.5 Add tests proving no provider key or project-root runtime database is created by fixture-only HITL tests.

## 10. Documentation And Validation

- [x] 10.1 Update README/server docs with Stage 05 HITL startup, API, reconnect, and fixture demo instructions.
- [x] 10.2 Update frontend/shared contract docs with Stage 05 event and interrupt payload descriptions.
- [x] 10.3 Run backend tests for graph runtime, run API, storage/replay, tools, skills, provider fallback, and HITL resume.
- [x] 10.4 Run frontend tests and typecheck after TypeScript/UI changes.
- [x] 10.5 Run `openspec validate "stage-05-hitl-sse-streaming" --strict`.
- [x] 10.6 Run `openspec status --change "stage-05-hitl-sse-streaming"` and confirm all artifacts are complete.
- [x] 10.7 Record verification commands and results in the implementation summary.
