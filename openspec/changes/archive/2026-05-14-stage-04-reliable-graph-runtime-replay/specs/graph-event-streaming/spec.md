## MODIFIED Requirements

### Requirement: Graph events map to Kira events

The system SHALL map graph execution activity into normalized Kira events that include thread ID, persisted sequence number, type, data, timestamp, and reliability metadata when applicable.

#### Scenario: Graph run emits ordered events

- **WHEN** a skill graph run streams graph activity
- **THEN** the SSE stream emits normalized Kira events in monotonically increasing persisted sequence order for the run thread

#### Scenario: Graph run emits completion

- **WHEN** a skill graph reaches its terminal path
- **THEN** the SSE stream emits exactly one terminal `done`, `error`, or cancelled event sequence for that graph run

### Requirement: Graph event contracts avoid future-stage persistence claims

The system SHALL support Stage 04 reliability events and persisted event replay while avoiding Stage 05+ HITL UI, retrieval, or memory event semantics.

#### Scenario: Checkpoint and retry events are allowed in Stage 04

- **WHEN** a Stage 04 graph run checkpoints, retries, cancels, or reuses a side effect
- **THEN** the event stream may emit structured reliability events or structured event payloads for those activities

#### Scenario: Future-stage events remain excluded

- **WHEN** a Stage 04 graph run streams events
- **THEN** it does not emit project retrieval, memory, or user-facing HITL approval events that belong to later stages

## ADDED Requirements

### Requirement: Persisted event replay

The system SHALL replay persisted Kira events by `thread_id` and event sequence without re-running graph nodes, tools, providers, or side effects.

#### Scenario: Replay reads stored events

- **WHEN** replay is requested for a run
- **THEN** the backend returns stored events in sequence order

#### Scenario: Replay does not re-run tool

- **WHEN** a replay includes a previous graph tool result
- **THEN** the tool is not executed again
