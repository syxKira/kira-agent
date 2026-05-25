## ADDED Requirements

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
