## ADDED Requirements

### Requirement: Graph events map to Kira events

The system SHALL map graph execution activity into normalized Kira events that include thread ID, sequence number, type, data, and timestamp.

#### Scenario: Graph run emits ordered events

- **WHEN** a skill graph run streams graph activity
- **THEN** the SSE stream emits normalized Kira events in monotonically increasing sequence order for the run thread

#### Scenario: Graph run emits completion

- **WHEN** a skill graph reaches its terminal path
- **THEN** the SSE stream emits exactly one `done` event for that graph run

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

The system SHALL NOT emit Stage 04 persistence events or claim durable replay behavior as part of Stage 03 graph streaming.

#### Scenario: No checkpoint events in Stage 03

- **WHEN** a Stage 03 graph run streams events
- **THEN** it does not emit checkpoint, resume, side-effect reuse, or replay events
