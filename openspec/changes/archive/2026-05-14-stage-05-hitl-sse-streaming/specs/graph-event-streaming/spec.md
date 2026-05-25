## ADDED Requirements

### Requirement: LangGraph astream events map to Kira events

The system SHALL map LangGraph `astream_events` output into normalized Kira events without exposing raw LangGraph callback payloads to the frontend.

#### Scenario: Graph lifecycle events are normalized

- **WHEN** a skill graph emits LangGraph start, stream, tool, checkpoint, interrupt, retry, or end events
- **THEN** the backend maps them to Kira event types such as `thinking_delta`, `text_delta`, `tool_start`, `tool_result`, `checkpoint`, `interrupt`, `retry`, `done`, or `error`
- **THEN** each event includes `thread_id`, monotonic `seq`, `type`, and redacted `data`

#### Scenario: Unknown graph event is tolerated

- **WHEN** LangGraph emits an event name that Kira does not render directly
- **THEN** the mapper either ignores it or converts it into a redacted debug/status event
- **THEN** the frontend stream does not crash

### Requirement: Events persist before SSE delivery

The system SHALL persist each normalized graph event before sending it over SSE.

#### Scenario: Interrupt persists before client receives it

- **WHEN** a graph reaches a human interrupt
- **THEN** the backend stores the `interrupt` event with the next sequence number before writing the SSE frame

#### Scenario: Stream failure can replay persisted events

- **WHEN** an SSE connection drops after events were persisted
- **THEN** reconnecting with `after_seq` replays missed persisted events in sequence order before live execution continues

### Requirement: Provider stream semantics survive graph mapping

The system SHALL preserve existing provider stream mapping inside graph event streaming.

#### Scenario: Visible provider text remains text delta

- **WHEN** a model node streams visible assistant content from the selected provider
- **THEN** graph event mapping emits `text_delta` events for visible content

#### Scenario: Hidden provider thinking stays separated

- **WHEN** a model node streams reasoning, thinking, or `<think>` content from the selected provider
- **THEN** graph event mapping emits `thinking_delta` events
- **THEN** hidden thinking is not merged into visible assistant answer text

#### Scenario: Provider upstream failure remains structured

- **WHEN** provider streaming fails due to HTTP, timeout, parse, or retry exhaustion errors
- **THEN** graph event mapping emits a structured `error` event with failure class metadata and redacted provider details

### Requirement: HITL graph streams include resume markers

The system SHALL emit visible event markers for human interruptions and submitted resume decisions.

#### Scenario: Interrupt and resume appear in order

- **WHEN** a graph run pauses for approval and the user later approves it
- **THEN** the persisted event sequence contains `interrupt` before `resume`
- **THEN** graph continuation events appear after the `resume` event

#### Scenario: Rejection produces structured result

- **WHEN** a user rejects an approval interrupt
- **THEN** the stream emits a `resume` event followed by a structured tool or workflow result explaining the rejection path
