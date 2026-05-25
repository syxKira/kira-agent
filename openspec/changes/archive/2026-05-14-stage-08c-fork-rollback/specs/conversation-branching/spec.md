## ADDED Requirements

### Requirement: Conversations can fork from an active-chain message
The system SHALL allow a client to create a new conversation forked from a selected message or turn on an existing conversation's active parent chain.

#### Scenario: Fork from message creates new conversation
- **WHEN** a client forks conversation A from a selected active-chain message
- **THEN** the backend creates conversation B with a unique `conversation_id`
- **THEN** conversation B records source conversation ID, source message ID, source turn ID when available, and source active head ID
- **THEN** conversation B active head points to the selected fork message or an equivalent provenance-linked head

#### Scenario: Fork rejects inactive source
- **WHEN** a client requests a fork from a message outside the source conversation active chain
- **THEN** the backend returns a structured validation error
- **THEN** no new conversation, branch record, transcript part, provider call, tool call, or memory record is created

### Requirement: Conversations can roll back active head non-destructively
The system SHALL allow a client to move a conversation's active head back to a selected message on the current active parent chain without deleting later transcript records.

#### Scenario: Rollback moves active head
- **WHEN** a client rolls back a conversation to a selected active-chain message
- **THEN** the conversation active head becomes that message
- **THEN** a rollback transition record is stored with previous active head, new active head, reason metadata, and timestamps

#### Scenario: Rollback preserves abandoned messages
- **WHEN** rollback moves active head before later messages
- **THEN** later messages remain readable from transcript APIs
- **THEN** later messages are omitted from future provider context unless they become active through a later explicit branch action

### Requirement: New runs continue from the selected active head
The system SHALL parent new user messages from the current conversation active head after fork or rollback.

#### Scenario: Run after rollback uses rollback head
- **WHEN** a conversation is rolled back and a new run is created in that conversation
- **THEN** the new user message parent points to the rollback head
- **THEN** abandoned later messages are not ancestors of the new turn

#### Scenario: Run in fork is isolated from source future
- **WHEN** a run is created in a forked conversation
- **THEN** provider context includes only inherited active-chain context up to the fork point and fork-local future messages
- **THEN** source conversation messages created after the fork point are not injected

### Requirement: Branch status is frontend-safe and inspectable
The system SHALL expose frontend-safe branch status and provenance metadata for fork source messages, active messages, rolled-back messages, and inactive branch messages.

#### Scenario: Transcript exposes branch metadata
- **WHEN** a client reads a transcript after fork or rollback
- **THEN** messages include branch status or branch metadata sufficient to distinguish active-chain, fork-source, and inactive messages
- **THEN** raw provider secrets and hidden thinking are not exposed

### Requirement: Branch operations do not create memory automatically
The system SHALL NOT create Stage 07 memory records from fork or rollback operations.

#### Scenario: Fork and rollback do not write memory
- **WHEN** a fork or rollback operation completes
- **THEN** no memory record is created unless a separate explicit memory write or approved memory candidate occurs
