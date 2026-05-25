# graph-event-streaming Specification

## Purpose
TBD - created by archiving change stage-03-skill-driven-langgraph-runtime. Update Purpose after archive.
## Requirements
### Requirement: Graph events map to Kira events

The system SHALL map graph execution activity into normalized Kira events that include thread ID, persisted sequence number, type, data, timestamp, and reliability metadata when applicable.

#### Scenario: Graph run emits ordered events

- **WHEN** a skill graph run streams graph activity
- **THEN** the SSE stream emits normalized Kira events in monotonically increasing persisted sequence order for the run thread

#### Scenario: Graph run emits completion

- **WHEN** a skill graph reaches its terminal path
- **THEN** the SSE stream emits exactly one terminal `done`, `error`, or cancelled event sequence for that graph run

### Requirement: Model output uses provider event mapping

The system SHALL map model-using graph node output through the existing provider event mapping, where visible assistant content becomes `text_delta`, hidden thinking becomes `thinking_delta`, normal completion becomes `done` or graph completion state, and upstream failures become structured errors.

#### Scenario: Visible model output is text delta

- **WHEN** a graph model node receives visible assistant content from the selected provider
- **THEN** the event stream emits `text_delta` payloads for visible content

#### Scenario: Hidden model thinking is separated

- **WHEN** a graph model node receives reasoning, thinking, or `<think>` content
- **THEN** the event stream emits `thinking_delta` payloads and does not merge hidden thinking into normal assistant answer text

### Requirement: Provider selection metadata is redacted in graph events

The system SHALL include selected provider/model metadata in graph run events only in redacted public form.

#### Scenario: Real provider graph run includes redacted metadata

- **WHEN** a graph run uses a configured real provider
- **THEN** emitted event payloads may include provider name, preset, selected model, source, and redacted key indicator
- **THEN** emitted event payloads do not include raw API keys

#### Scenario: Fixture fallback graph run includes fallback reason

- **WHEN** a graph run falls back to the fixture provider because no valid API key is available
- **THEN** emitted event payloads include fixture mode and fallback reason metadata

### Requirement: Graph failures produce structured errors

The system SHALL convert graph validation failures, runtime exceptions, provider failures, and tool failures into structured `error` events or structured run creation errors.

#### Scenario: Runtime exception becomes error event

- **WHEN** a compiled graph raises an unexpected runtime exception during event streaming
- **THEN** the SSE stream emits an `error` event with a code and message

#### Scenario: Provider failure becomes graph error

- **WHEN** a graph model node receives a provider HTTP, timeout, parse, or retry exhaustion failure
- **THEN** the graph stream emits a structured `error` event without exposing secrets

### Requirement: Existing non-graph streams are preserved

The system SHALL preserve the existing provider/fixture streaming behavior for runs that do not select a workflow-capable skill.

#### Scenario: Fixture run remains deterministic

- **WHEN** a run is created with an explicit fixture and no `skill_id`
- **THEN** the stream follows the existing deterministic fixture event sequence

#### Scenario: Direct provider run remains available

- **WHEN** a run is created with no `skill_id` and a valid real provider is configured
- **THEN** the stream follows the existing direct provider streaming path

### Requirement: Graph event contracts avoid future-stage persistence claims

The system SHALL support Stage 04 reliability events and persisted event replay while avoiding Stage 05+ HITL UI, retrieval, or memory event semantics.

#### Scenario: Checkpoint and retry events are allowed in Stage 04

- **WHEN** a Stage 04 graph run checkpoints, retries, cancels, or reuses a side effect
- **THEN** the event stream may emit structured reliability events or structured event payloads for those activities

#### Scenario: Future-stage events remain excluded

- **WHEN** a Stage 04 graph run streams events
- **THEN** it does not emit project retrieval, memory, or user-facing HITL approval events that belong to later stages

### Requirement: Persisted event replay

The system SHALL replay persisted Kira events by `thread_id` and event sequence without re-running graph nodes, tools, providers, or side effects.

#### Scenario: Replay reads stored events

- **WHEN** replay is requested for a run
- **THEN** the backend returns stored events in sequence order

#### Scenario: Replay does not re-run tool

- **WHEN** a replay includes a previous graph tool result
- **THEN** the tool is not executed again

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

