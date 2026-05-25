## ADDED Requirements

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
