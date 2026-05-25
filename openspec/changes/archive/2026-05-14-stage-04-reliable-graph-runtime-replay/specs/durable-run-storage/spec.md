## ADDED Requirements

### Requirement: Local SQLite runtime storage

The system SHALL provide a Kira-owned local SQLite database for reliable graph runtime records, with an overridable path for tests and local development.

#### Scenario: Default storage initializes
- **WHEN** the backend starts with no explicit test database path
- **THEN** it initializes runtime storage under a Kira-owned user-local location, not the project root

#### Scenario: Test storage override initializes
- **WHEN** tests provide a temporary database path
- **THEN** migrations run against that path without reading or writing user-local runtime data

### Requirement: Runtime migrations

The system SHALL apply idempotent SQLite migrations for checkpoints, run events, run attempts, provider attempts, run locks, side-effect ledger entries, projections, and repair notes.

#### Scenario: Migrations are idempotent
- **WHEN** the backend applies migrations more than once
- **THEN** the schema remains valid and existing runtime records are preserved

#### Scenario: Missing table is created
- **WHEN** a fresh runtime database is opened
- **THEN** all Stage 04 runtime tables are created before graph execution starts

### Requirement: Checkpoint integration

The system SHALL compile Stage 04 graph runs with a SQLite-backed LangGraph checkpointer and SHALL use checkpointed graph state as the authoritative execution state.

#### Scenario: Graph checkpoint is written
- **WHEN** a graph run reaches a checkpoint boundary
- **THEN** checkpoint state is persisted for the run `thread_id`

#### Scenario: Projection is derived
- **WHEN** the state projection is read
- **THEN** it is derived from checkpoint, event, attempt, provider, and ledger records rather than being the only source of truth

### Requirement: Run event persistence

The system SHALL persist normalized Kira events with monotonically increasing `seq` values per `thread_id`.

#### Scenario: Events are persisted before stream
- **WHEN** a graph event is emitted
- **THEN** it is assigned the next sequence number and persisted before it is streamed to the client

#### Scenario: Sequence is stable after restart
- **WHEN** the backend restarts after events were persisted
- **THEN** replay reads the same sequence numbers for that `thread_id`

### Requirement: Redacted provider attempt storage

The system SHALL persist provider attempt metadata in redacted form, including provider profile identifier, model, timeout, retry count, fallback flag, status, and redacted error summary.

#### Scenario: Provider attempt omits raw key
- **WHEN** a provider attempt is stored
- **THEN** no raw API key or raw provider config object is stored

#### Scenario: Fixture fallback is stored
- **WHEN** provider selection falls back to fixture mode
- **THEN** the provider attempt record includes fixture fallback status and reason
