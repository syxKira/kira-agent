# openai-compatible-streaming Specification

## Purpose
TBD - created by archiving change add-real-llm-provider. Update Purpose after archive.
## Requirements
### Requirement: Stream from OpenAI-compatible API

The system SHALL call an OpenAI-compatible streaming chat completions API from the local FastAPI server using selected provider config.

#### Scenario: Remote stream produces Kira events

- **WHEN** a selected real provider returns valid streaming chat completion chunks
- **THEN** the backend emits ordered SSE Kira events for the run

### Requirement: Map visible assistant content

The system SHALL map visible assistant content from remote chunks into `text_delta` events.

#### Scenario: Content delta becomes text delta

- **WHEN** an upstream chunk contains visible assistant content
- **THEN** the backend emits a `text_delta` event containing that visible content

### Requirement: Map hidden thinking separately

The system SHALL map hidden thinking from `reasoning_content`, thinking fields, or `<think>...</think>` content into `thinking_delta` events.

#### Scenario: Reasoning content becomes thinking delta

- **WHEN** an upstream chunk contains `reasoning_content` or an equivalent thinking field
- **THEN** the backend emits `thinking_delta` and does not merge that text into `text_delta`

#### Scenario: Think tags become thinking delta

- **WHEN** visible content contains `<think>hidden</think>` sections
- **THEN** the backend emits hidden sections as `thinking_delta` and visible sections as `text_delta`

#### Scenario: Split think tags are parsed

- **WHEN** `<think>` or `</think>` tags are split across streaming chunks
- **THEN** the parser still emits hidden text as `thinking_delta` and does not leak it into visible text

### Requirement: Emit done on normal completion

The system SHALL emit a `done` event when an upstream stream completes normally.

#### Scenario: Finish reason emits done

- **WHEN** the upstream stream reports normal completion or reaches `[DONE]`
- **THEN** the backend emits exactly one terminal `done` event for the run

### Requirement: Emit structured provider errors

The system SHALL map upstream HTTP, API, timeout, retry exhaustion, and parse failures into structured `error` events.

#### Scenario: Non-2xx response emits provider error

- **WHEN** upstream returns a non-2xx response
- **THEN** the backend emits an `error` event with redacted provider error metadata

#### Scenario: Timeout emits provider error

- **WHEN** upstream request or stream reading times out
- **THEN** the backend emits an `error` event with code `provider_timeout`

#### Scenario: Malformed stream emits provider error

- **WHEN** upstream stream contains malformed JSON or unsupported payload structure
- **THEN** the backend emits an `error` event with code `provider_parse_error`

#### Scenario: Retry exhaustion emits provider error

- **WHEN** configured retries are exhausted before a successful stream starts
- **THEN** the backend emits an `error` event with code `provider_retry_exhausted`

### Requirement: Verify without real API key by default

The system SHALL use mocks for default tests and SHALL skip real smoke tests unless explicit env/config opt-in is present.

#### Scenario: Default tests do not need API key

- **WHEN** the backend test suite runs without real provider credentials
- **THEN** all normal tests pass using fixtures or mocked upstream streams

#### Scenario: Real smoke test is opt-in

- **WHEN** real smoke test opt-in env/config is absent
- **THEN** the real provider smoke test is skipped

