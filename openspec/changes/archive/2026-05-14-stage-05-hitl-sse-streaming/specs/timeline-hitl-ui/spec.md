## ADDED Requirements

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
