## ADDED Requirements

### Requirement: Resume detects inactive-branch conflicts
The resume API SHALL detect when an interrupted `thread_id` belongs to a conversation turn that is no longer on the conversation active parent chain.

#### Scenario: Resume outside active chain conflicts
- **WHEN** a run is interrupted, the conversation is rolled back before that turn, and a client attempts to resume the interrupted `thread_id`
- **THEN** the backend returns a structured resume conflict
- **THEN** no continuation events, transcript parts, provider calls, tool calls, or memory records are created

#### Scenario: Resume inside active chain continues
- **WHEN** an interrupted run's turn remains on the conversation active chain
- **THEN** the resume API continues the existing `thread_id` and turn
- **THEN** no new user message or conversation turn is created

### Requirement: Resume conflict metadata is frontend-safe
The system SHALL return frontend-safe conflict metadata describing the interrupted turn, current active head, and branch transition that caused the conflict.

#### Scenario: Conflict response is redacted
- **WHEN** resume conflict metadata is returned
- **THEN** it includes thread ID, conversation ID, turn ID, current active head ID, and relevant transition ID when available
- **THEN** it excludes raw provider secrets, hidden thinking, and unbounded transcript text
