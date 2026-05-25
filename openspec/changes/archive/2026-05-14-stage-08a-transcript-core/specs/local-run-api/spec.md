## ADDED Requirements

### Requirement: Runs support conversation continuity
The run creation API SHALL accept an optional `conversation_id` and SHALL return `conversation_id` and `turn_id` in the run creation response.

#### Scenario: Run reuses existing conversation
- **WHEN** a client creates a run with an existing active `conversation_id`
- **THEN** the backend creates a new turn in that conversation
- **THEN** the response includes the same `conversation_id`, a new `turn_id`, and a new `thread_id`

#### Scenario: Run creates conversation when omitted
- **WHEN** a client creates a run without `conversation_id`
- **THEN** the backend creates a new conversation
- **THEN** the response includes the created `conversation_id` and `turn_id`

#### Scenario: Unknown conversation is rejected
- **WHEN** a client creates a run with an unknown or archived `conversation_id`
- **THEN** the backend returns a structured validation or not-found error
- **THEN** no provider, graph, tool, memory retrieval, or project retrieval work is started

### Requirement: Conversation APIs are available
The system SHALL expose local API endpoints for creating, listing, reading, updating metadata, reading transcript, and inspecting conversation context.

#### Scenario: Conversation transcript endpoint
- **WHEN** a client requests `GET /api/conversations/{conversation_id}/transcript`
- **THEN** the backend returns bounded ordered transcript messages and parts for that conversation

#### Scenario: Conversation context endpoint
- **WHEN** a client requests `GET /api/conversations/{conversation_id}/context`
- **THEN** the backend returns a frontend-safe explanation of transcript ContextItems that would be eligible for the next run

### Requirement: Run context trace exposes transcript usage
The run context trace API SHALL show included, truncated, and omitted conversation history and tool summary ContextItems.

#### Scenario: Context trace returns transcript items
- **WHEN** a client requests context trace for a run that used conversation history
- **THEN** the response includes conversation ID, turn IDs, message IDs, ContextItem kinds, trust labels, budget costs, and omission reasons

### Requirement: Resume remains thread-scoped inside conversations
The resume API SHALL continue an existing interrupted `thread_id` and SHALL NOT create a new conversation turn.

#### Scenario: Resume keeps turn link
- **WHEN** a client posts a valid resume decision for a run linked to a conversation
- **THEN** the resume event is linked to the existing turn
- **THEN** no new user message is created
