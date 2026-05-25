## ADDED Requirements

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
