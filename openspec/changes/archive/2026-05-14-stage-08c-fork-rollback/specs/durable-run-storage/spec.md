## ADDED Requirements

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
