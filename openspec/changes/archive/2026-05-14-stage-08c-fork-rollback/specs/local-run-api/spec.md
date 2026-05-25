## ADDED Requirements

### Requirement: Conversation fork API is available
The system SHALL expose a local API endpoint for forking a conversation from a selected active-chain message or turn.

#### Scenario: Fork endpoint creates conversation
- **WHEN** a client posts to `POST /api/conversations/{conversation_id}/fork` with a valid source message or turn
- **THEN** the backend creates a new conversation
- **THEN** the response includes new conversation ID, source conversation ID, source message ID, source turn ID when available, and active head metadata

#### Scenario: Fork endpoint rejects invalid source
- **WHEN** a client forks from an unknown, archived, or inactive source
- **THEN** the backend returns a structured validation or not-found error
- **THEN** no new conversation, transcript part, provider call, tool call, or memory record is created

### Requirement: Conversation rollback API is available
The system SHALL expose a local API endpoint for moving a conversation active head to a selected active-chain message or turn.

#### Scenario: Rollback endpoint moves active head
- **WHEN** a client posts to `POST /api/conversations/{conversation_id}/rollback` with a valid target message
- **THEN** the backend updates the conversation active head
- **THEN** the response includes previous active head, new active head, transition ID, and frontend-safe inactive branch summary

#### Scenario: Rollback endpoint rejects invalid target
- **WHEN** a client rolls back to an unknown, archived, or inactive target
- **THEN** the backend returns a structured validation or not-found error
- **THEN** the conversation active head is unchanged

### Requirement: Run creation honors branch active head
The run creation API SHALL parent new turns from the selected conversation's current active head after fork or rollback.

#### Scenario: Run after rollback excludes abandoned future
- **WHEN** a client creates a run after rollback
- **THEN** the backend links the new user message to the rollback head
- **THEN** run context excludes messages abandoned by the rollback

### Requirement: APIs expose branch context safely
Conversation transcript, conversation context, and run context APIs SHALL expose frontend-safe branch metadata without raw provider secrets or hidden thinking.

#### Scenario: Context endpoint shows inactive branch omission
- **WHEN** a client requests context for a conversation with inactive branch messages
- **THEN** the response explains active head, fork/rollback metadata, included active-chain items, and omitted inactive branch items
