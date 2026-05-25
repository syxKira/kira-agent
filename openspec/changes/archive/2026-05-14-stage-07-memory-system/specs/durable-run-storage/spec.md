## ADDED Requirements

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
