## ADDED Requirements

### Requirement: Render HITL timeline states

The workbench SHALL render Stage 05 interrupt and resume events as first-class timeline states.

#### Scenario: Interrupt row appears in timeline

- **WHEN** the event stream emits an `interrupt` event
- **THEN** the timeline shows a waiting-for-user row with the interrupt title and kind

#### Scenario: Resume row appears in timeline

- **WHEN** the event stream emits a `resume` event
- **THEN** the timeline shows a user decision marker without exposing raw internal resume payloads

### Requirement: Render active HITL control panel

The workbench SHALL show an active HITL control panel when the latest unresolved event is an interrupt.

#### Scenario: Approval controls are usable

- **WHEN** an approval interrupt is active
- **THEN** the panel provides approve and reject controls that are reachable by keyboard and pointer

#### Scenario: Edit controls preserve suggested content

- **WHEN** an edit interrupt is active
- **THEN** the panel initializes editable text from the interrupt payload and allows the user to submit a bounded edited value

#### Scenario: Question controls submit answer

- **WHEN** a question interrupt is active
- **THEN** the panel allows the user to enter and submit an answer matching the declared response fields

### Requirement: Workbench remains compatible with previous events

The workbench SHALL continue to render Stage 01 fixture, Stage 03 graph tool, Stage 04 replay, and direct provider events while adding Stage 05 HITL rendering.

#### Scenario: Fixture run still renders

- **WHEN** a run emits only Stage 01 fixture-style events
- **THEN** the workbench renders the existing timeline without requiring HITL state

#### Scenario: Side-effect reuse remains a tool/status block

- **WHEN** a run emits `side_effect_reused`
- **THEN** the workbench renders it as a non-answer status/tool block

#### Scenario: Provider metadata remains redacted

- **WHEN** timeline or panel payloads include provider metadata
- **THEN** raw API keys do not appear in the DOM
