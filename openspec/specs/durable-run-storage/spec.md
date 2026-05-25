# durable-run-storage Specification

## Purpose
TBD - created by archiving change stage-04-reliable-graph-runtime-replay. Update Purpose after archive.
## Requirements
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

### Requirement: Local SQLite stores memory records
The system SHALL add idempotent SQLite migrations for memory records, memory events, memory citations, memory tombstones, retrieval traces, and extraction candidates.

#### Scenario: Fresh database creates memory tables
- **WHEN** runtime storage initializes on a fresh database
- **THEN** all Stage 07 memory tables are created before memory APIs are used

#### Scenario: Migration preserves existing runtime data
- **WHEN** Stage 07 migrations run on a database with Stage 04-06 runtime records
- **THEN** existing run events, projections, checkpoints, project index records, and context traces remain intact

### Requirement: Memory storage is Kira-owned
The system SHALL write memory records only to Kira-owned SQLite/cache storage and SHALL NOT write generated memory files into project roots.

#### Scenario: Memory write does not mutate project
- **WHEN** a memory record is created, updated, deleted, merged, or promoted
- **THEN** the backend writes only to Kira-owned storage and does not write, move, delete, patch, format, or stage project files

### Requirement: Memory storage is redacted
The system SHALL ensure raw API keys, tokens, cookies, private keys, `.env` values, raw provider configs, and unredacted upstream errors are absent from persisted memory tables.

#### Scenario: Storage redaction test scans memory tables
- **WHEN** tests inspect persisted memory rows after rejected and accepted memory operations
- **THEN** raw secret fixtures are absent from all memory tables

### Requirement: Store conversation transcript tables locally
The system SHALL add Kira-owned SQLite tables for conversations, turns, transcript messages, transcript parts, conversation-run links, and transcript context traces.

#### Scenario: Transcript tables are created
- **WHEN** runtime storage initializes on a fresh database
- **THEN** conversation and transcript tables exist alongside prior run, project, and memory tables

#### Scenario: Migrations are idempotent
- **WHEN** storage migrations run multiple times
- **THEN** transcript tables remain valid and existing records are preserved

### Requirement: Preserve prior runtime data through transcript migrations
The system SHALL preserve Stage 04 run records, Stage 06 project index records, and Stage 07 memory records when Stage 08a transcript migrations are applied.

#### Scenario: Existing records survive migration
- **WHEN** a database with existing run, project, and memory tables is migrated
- **THEN** those records remain readable
- **THEN** the new transcript tables are available

### Requirement: Link runs to conversations durably
The system SHALL persist a durable mapping between `conversation_id`, `turn_id`, and `thread_id`.

#### Scenario: Run link is queryable
- **WHEN** a run is created in a conversation
- **THEN** storage can resolve the run's conversation and turn from `thread_id`
- **THEN** storage can list all runs for a conversation or turn

### Requirement: Transcript storage is redacted and bounded
The system SHALL store transcript parts with bounded text, visible flags, role/kind metadata, and redacted payloads.

#### Scenario: Secret-like payload is redacted
- **WHEN** a transcript part is created from provider metadata, tool output, error payload, or runtime marker
- **THEN** raw API keys, authorization headers, cookies, and provider config secrets are absent from stored text and payload

#### Scenario: Oversized part is bounded
- **WHEN** a transcript part source exceeds configured text limits
- **THEN** storage keeps a truncated summary or marker with omission metadata instead of unbounded raw text

### Requirement: Store compaction summaries locally
The system SHALL add Kira-owned SQLite storage for conversation compaction summaries with source ranges, hashes, tail boundaries, token estimates, summarizer metadata, status, stale reason, previous summary link, and timestamps.

#### Scenario: Compaction tables are created
- **WHEN** runtime storage initializes on a fresh database
- **THEN** compaction summary storage exists alongside prior run, project, memory, and transcript tables

#### Scenario: Compaction migration is idempotent
- **WHEN** storage migrations run multiple times
- **THEN** compaction summary tables and indexes remain valid
- **THEN** existing transcript, memory, project, and run records remain readable

### Requirement: Store tool-output replacement records locally
The system SHALL add Kira-owned SQLite storage for tool-output replacement records with source references, replacement summary, output hash, omitted counts, reason, retention policy, redacted reference metadata, status, and timestamps.

#### Scenario: Replacement tables are created
- **WHEN** runtime storage initializes on a fresh database
- **THEN** tool-output replacement storage exists and can link records to conversation, turn, thread, message, and part IDs

#### Scenario: Replacement migration preserves existing data
- **WHEN** a database with Stage 04 through Stage 08a records is migrated
- **THEN** prior records remain readable
- **THEN** replacement records can be inserted without requiring raw provider secrets or raw tool output

### Requirement: Compaction and replacement records are redacted
The system SHALL redact secrets from compaction summaries, replacement summaries, metadata, traces, and stored payloads before persistence.

#### Scenario: Secret-like replacement output is guarded
- **WHEN** replacement is created from text containing API keys, cookies, bearer tokens, private keys, or provider config
- **THEN** the persisted summary and metadata omit raw secret values
- **THEN** stored frontend-safe metadata contains only redacted references and hashes

### Requirement: Store conversation branch records locally
The system SHALL add Kira-owned SQLite storage for conversation branch records with operation type, source conversation ID, target conversation ID, source message ID, source turn ID, previous active head ID, new active head ID, reason metadata, status, and timestamps.

#### Scenario: Branch tables are created
- **WHEN** runtime storage initializes on a fresh database
- **THEN** branch and active-head transition storage exists alongside prior run, transcript, compaction, replacement, project, and memory tables

#### Scenario: Branch migration preserves existing data
- **WHEN** a database with Stage 04 through Stage 08b records is migrated
- **THEN** prior records remain readable
- **THEN** branch records can be inserted without requiring provider calls or memory writes

### Requirement: Store active-head transitions durably
The system SHALL store every fork or rollback active-head transition with enough metadata to reconstruct why the active head changed.

#### Scenario: Rollback transition is queryable
- **WHEN** rollback moves active head from one message to another
- **THEN** storage can query the transition by conversation ID and transition ID
- **THEN** the transition includes previous active head, new active head, operation type, timestamp, and redacted reason metadata

### Requirement: Branch storage is redacted and bounded
The system SHALL keep branch metadata frontend-safe and SHALL NOT store raw provider secrets, hidden thinking, or unbounded transcript text in branch records.

#### Scenario: Branch reason is redacted
- **WHEN** a fork or rollback reason contains secret-like text
- **THEN** storage redacts the secret-like values before persistence
- **THEN** frontend branch metadata remains bounded

