# timeline-hitl-ui Specification

## Purpose
TBD - created by archiving change stage-05-hitl-sse-streaming. Update Purpose after archive.
## Requirements
### Requirement: Timeline renders Stage 05 graph events

The frontend SHALL render normalized Stage 05 Kira events as timeline blocks without depending on raw LangGraph event names or provider chunk shapes.

#### Scenario: Tool and status events render as structured blocks

- **WHEN** the event stream emits `tool_start`, `tool_result`, `retry`, `checkpoint`, or `side_effect_reused`
- **THEN** the timeline renders compact status rows or tool cards appropriate to the event type
- **THEN** unbounded raw payloads are collapsed or truncated by default

#### Scenario: Hidden thinking remains out of answers

- **WHEN** the event stream emits `thinking_delta` before, during, or after HITL events
- **THEN** the timeline does not render hidden thinking as normal assistant answer text

### Requirement: HITL panel renders pending decisions

The frontend SHALL render a focused HITL panel for approval, edit, question, and Python approval interrupt payloads.

#### Scenario: Approval panel is shown

- **WHEN** the timeline receives an `interrupt` event with `kind: "approval"`
- **THEN** the workbench shows a waiting timeline row and a focused panel with approve and reject actions

#### Scenario: Edit panel is shown

- **WHEN** the timeline receives an `interrupt` event with `kind: "edit"`
- **THEN** the workbench shows editable text initialized from the interrupt payload and a submit action for the edited value

#### Scenario: Question panel is shown

- **WHEN** the timeline receives an `interrupt` event with `kind: "question"`
- **THEN** the workbench shows the question body and response fields declared by the interrupt payload

### Requirement: HITL submissions call resume API

The frontend SHALL submit human decisions to the backend resume endpoint and update the workbench from streamed events.

#### Scenario: Approval submission resumes stream

- **WHEN** the user approves a pending interrupt
- **THEN** the frontend posts the matching `interrupt_id` and decision to `POST /api/runs/{thread_id}/resume`
- **THEN** the timeline receives a persisted `resume` marker followed by continued graph events

#### Scenario: Resume error remains actionable

- **WHEN** the resume endpoint returns a validation error or lock conflict
- **THEN** the workbench shows a concise error state without discarding the pending interrupt context

### Requirement: Workbench tolerates reconnect and replay

The frontend SHALL use event sequence cursors to avoid duplicate timeline blocks when reconnecting to a HITL run.

#### Scenario: Missed interrupt is replayed once

- **WHEN** the browser reconnects with the last seen event sequence before an interrupt
- **THEN** the backend replays the missed interrupt event
- **THEN** the frontend renders one pending HITL panel for that interrupt

#### Scenario: Completed resume replay is read-only

- **WHEN** the frontend loads replay data for a completed HITL run
- **THEN** interrupt and resume markers render as historical timeline events
- **THEN** the frontend does not show an active resume form for already resolved interrupts

### Requirement: HITL supports memory approval prompts
The frontend SHALL reuse the Stage 05 HITL approval/edit UI for memory write and promotion approvals when backend policy requires human approval.

#### Scenario: Memory promotion approval is shown
- **WHEN** the backend emits an interrupt for memory promotion approval
- **THEN** the frontend shows a focused approval panel with memory summary, target scope, approve/reject actions, and redacted metadata

#### Scenario: Memory candidate edit is shown
- **WHEN** the backend emits an edit interrupt for a memory extraction candidate
- **THEN** the frontend lets the user edit the candidate text before submitting the resume decision

### Requirement: Memory approval resume is persisted
The frontend SHALL submit memory approval decisions through the existing resume endpoint and render resume markers as normal timeline events.

#### Scenario: Approved memory write resumes run
- **WHEN** the user approves a pending memory approval interrupt
- **THEN** the frontend posts the matching `interrupt_id` and decision to the resume endpoint
- **THEN** the timeline receives a persisted resume marker and subsequent memory outcome events or summaries

### Requirement: Timeline renders event-specific Stage 10 cards and rows
The frontend SHALL map normalized Kira events to visually distinct Stage 10 timeline rows or cards without depending on raw provider or LangGraph payload shapes.

#### Scenario: Normalized events have distinct visual treatment
- **WHEN** the timeline receives `text_delta`, `thinking_delta`, `tool_start`, `tool_result`, `checkpoint`, `interrupt`, `resume`, `retry`, `side_effect_reused`, `error`, or `done` events
- **THEN** it SHALL render answer text, subdued thinking/status rows, compact tool-call rows, expandable tool-result cards, debug checkpoint markers, HITL waiting rows, user decision markers, retry attempt rows, reuse markers, error blocks, and completion rows as separate visual treatments

#### Scenario: Hidden thinking is not answer text
- **WHEN** `thinking_delta` and `text_delta` events are present in the same run
- **THEN** hidden thinking SHALL remain in subdued or collapsed thinking/status UI
- **THEN** hidden thinking SHALL NOT be merged into normal assistant answer text, persisted visible transcript rows, copyable answer content, or screenshot fixtures that represent final answers

### Requirement: Tool and retrieval outputs are bounded and inspectable
The frontend SHALL render tool results and project retrieval snippets in bounded cards with metadata, truncation or internal scrolling, expand/collapse behavior, and copy controls where safe.

#### Scenario: Long tool output does not break layout
- **WHEN** a `tool_result` contains long JSON or long text
- **THEN** the timeline SHALL show a bounded preview with tool name, status, content type, truncation metadata when available, and an expand/collapse or internal-scroll affordance
- **THEN** the card SHALL wrap text and preserve adjacent controls without visual overlap at desktop and narrow widths

#### Scenario: Retrieval snippet shows citation metadata
- **WHEN** project knowledge or context trace data includes cited retrieval snippets, stale markers, omitted items, or truncation metadata
- **THEN** the timeline or inspector SHALL show source path, line or chunk metadata when available, stale or omission reason, and bounded snippet preview without exposing raw internal index rows

### Requirement: HITL timeline and panel match Stage 10 shell
The frontend SHALL render HITL interrupts and resume markers as first-class dark-shell timeline states with a focused, keyboard-accessible decision panel.

#### Scenario: Pending interrupt is visually prominent
- **WHEN** an unresolved `interrupt` event is the latest active HITL state
- **THEN** the timeline SHALL show a waiting row and the workbench SHALL show a focused HITL panel for approval, edit, question, or Python approval payloads using existing resume semantics

#### Scenario: Resolved interrupt becomes history
- **WHEN** a matching `resume` marker is present or a completed HITL run is replayed
- **THEN** the frontend SHALL render the interrupt and resume as historical timeline events
- **THEN** it SHALL NOT show an active resume form for an already resolved interrupt

### Requirement: Retry, reuse, error, cancellation, and reconnect states are distinguishable
The frontend SHALL render retry attempts, reused side effects, errors, cancelled runs, reconnecting streams, and completion as visually distinct status states that do not masquerade as assistant answers.

#### Scenario: Reliability events are status rows
- **WHEN** the stream emits retry, side-effect reuse, cancellation, reconnect, error, or done information
- **THEN** the timeline SHALL render that information as compact status, debug, error, or terminal rows rather than normal assistant answer text
- **THEN** available retry, resume, inspect, or stop controls SHALL remain keyboard reachable when those actions already exist

