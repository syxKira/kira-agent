## ADDED Requirements

### Requirement: Define provider-neutral Stage 01 events

The system SHALL define shared Stage 01 event contracts for visible text, hidden thinking, completion, and errors.

#### Scenario: Provider events normalize to Kira events

- **WHEN** a provider emits text, thinking, done, or error output
- **THEN** the backend normalizes it to `text_delta`, `thinking_delta`, `done`, or `error` Kira events with a monotonic sequence number

### Requirement: Support deterministic fixture replay

The system SHALL provide a fixture provider that replays scripted events deterministically for local development and automated tests.

#### Scenario: Fixture run emits scripted sequence

- **WHEN** a run selects a known fixture script
- **THEN** the event stream emits the fixture events in the scripted order without calling a remote provider

#### Scenario: Fixture tests are repeatable

- **WHEN** backend tests execute fixture replay more than once
- **THEN** the visible event types and payload content are stable across runs except for unique run identifiers and timestamps

### Requirement: Provide an OpenAI-compatible provider boundary

The system SHALL include a provider interface suitable for an OpenAI-compatible streaming provider while keeping Stage 01 tests on fixture replay.

#### Scenario: Provider interface is independent of frontend rendering

- **WHEN** a provider implementation emits provider-specific stream chunks
- **THEN** frontend-facing events are produced only through the normalized Stage 01 Kira event contract

### Requirement: Protect hidden thinking from normal answer rendering

The system SHALL distinguish hidden thinking from visible assistant text at the event contract level.

#### Scenario: Thinking is not visible answer text

- **WHEN** a provider or fixture emits a `thinking_delta`
- **THEN** the event is available to the timeline as status/debug metadata and is not merged into normal assistant answer text
