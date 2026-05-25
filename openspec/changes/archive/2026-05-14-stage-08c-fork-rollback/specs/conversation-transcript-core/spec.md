## ADDED Requirements

### Requirement: Transcript stores fork markers safely
The system SHALL store fork provenance as frontend-safe transcript metadata or marker parts without changing visible assistant answer text.

#### Scenario: Fork marker is recorded
- **WHEN** a conversation is forked from a source message
- **THEN** the source conversation and forked conversation expose bounded fork metadata with source conversation ID, source message ID, source turn ID when available, and created fork conversation ID
- **THEN** the marker does not appear as normal assistant answer text

### Requirement: Transcript stores rollback markers safely
The system SHALL store rollback metadata or marker parts when active head moves backward without deleting or rewriting source messages.

#### Scenario: Rollback marker is recorded
- **WHEN** a conversation is rolled back
- **THEN** transcript APIs expose bounded rollback metadata with previous active head, new active head, affected turn/message IDs when available, and timestamp
- **THEN** original transcript messages remain readable

### Requirement: Transcript APIs distinguish active and inactive messages
The system SHALL expose enough frontend-safe branch metadata for clients to distinguish active-chain messages from inactive branch messages after fork or rollback.

#### Scenario: Read transcript after rollback
- **WHEN** a client reads a conversation transcript after rollback and new follow-up messages
- **THEN** the response includes active-chain and inactive branch metadata
- **THEN** hidden thinking and raw provider secrets remain excluded
