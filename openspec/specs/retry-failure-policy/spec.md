# retry-failure-policy Specification

## Purpose
TBD - created by archiving change stage-04-reliable-graph-runtime-replay. Update Purpose after archive.
## Requirements
### Requirement: Failure taxonomy

The system SHALL classify graph runtime failures into stable classes including `validation_error`, `permission_error`, `timeout_error`, `transient_external_error`, `provider_config_error`, `provider_stream_error`, `tool_error`, `side_effect_conflict`, `cancelled`, and `invariant_error`.

#### Scenario: Provider stream failure classified
- **WHEN** a provider stream returns malformed chunks or retry exhaustion
- **THEN** the graph runtime records a `provider_stream_error` or related provider failure class

#### Scenario: Path permission failure classified
- **WHEN** a tool rejects a forbidden file path
- **THEN** the graph runtime records a `permission_error` or tool-specific non-retryable failure class

### Requirement: Retry policy by class and idempotency

The system SHALL retry only retryable failure classes within configured limits and only when the node/tool/action is idempotent or protected by a stable idempotency key.

#### Scenario: Retryable timeout retries
- **WHEN** an idempotent node or tool fails with a timeout and attempts remain
- **THEN** the runtime retries with backoff and records retry attempt events

#### Scenario: Validation error does not retry
- **WHEN** a node or tool fails with validation error
- **THEN** the runtime records the failure and does not retry automatically

### Requirement: Timeout and backoff policy

The system SHALL enforce node/tool timeout hints and bounded retry backoff with a maximum attempt count.

#### Scenario: Timeout is surfaced
- **WHEN** a node exceeds its timeout hint
- **THEN** the event stream and state projection include timeout failure metadata

#### Scenario: Retry exhaustion is terminal
- **WHEN** retry attempts are exhausted
- **THEN** the run is marked failed and remains inspectable

### Requirement: Provider retry coordination

The system SHALL coordinate graph-level provider retries with the OpenAI-compatible provider adapter's configured timeout and retry budget.

#### Scenario: Provider adapter exhausts retry
- **WHEN** the provider adapter reports retry exhaustion
- **THEN** graph retry occurs only if the node is safe to repeat and policy still allows another attempt

#### Scenario: Provider attempt metadata persisted
- **WHEN** a provider call is attempted inside a graph node
- **THEN** redacted provider attempt metadata is persisted with retry count and final status

### Requirement: Failure metadata is redacted

The system SHALL redact secrets from failure metadata, retry events, provider attempts, state projection, and replay export.

#### Scenario: API key omitted from failure
- **WHEN** a provider failure contains text that resembles or includes an API key
- **THEN** persisted and emitted failure metadata redacts the key

