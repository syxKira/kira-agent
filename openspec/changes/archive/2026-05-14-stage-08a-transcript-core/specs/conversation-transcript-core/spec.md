## ADDED Requirements

### Requirement: Conversations define multi-turn continuity
The system SHALL represent a local multi-turn chat as a conversation identified by `conversation_id`, separate from run execution `thread_id`.

#### Scenario: New conversation is created
- **WHEN** a client creates a conversation without a title
- **THEN** the backend returns a unique `conversation_id`, active status, timestamps, and an empty transcript head

#### Scenario: Thread identifier remains run-scoped
- **WHEN** multiple prompts are submitted in the same conversation
- **THEN** each prompt creates its own `thread_id`
- **THEN** all created `thread_id` values remain linked to the same `conversation_id`

### Requirement: Turns link user requests to assistant runs
The system SHALL create a `turn_id` for each user request and SHALL link that turn to the conversation, user message, assistant message, and run `thread_id`.

#### Scenario: Run creates turn linkage
- **WHEN** a client creates a run in a conversation
- **THEN** the backend creates a turn record with `conversation_id`, `turn_id`, user message ID, and `thread_id`
- **THEN** the run creation response includes `conversation_id` and `turn_id`

#### Scenario: Resume does not create a new turn
- **WHEN** a client resumes an interrupted `thread_id`
- **THEN** the resume continues the existing turn linkage
- **THEN** no additional user turn is created

### Requirement: Transcript messages are parent-linked
The system SHALL persist transcript messages with stable message IDs, roles, status, parent links, and optional logical parent links.

#### Scenario: Linear message chain is recorded
- **WHEN** a user submits two prompts in one conversation
- **THEN** each new user message parent points to the prior active assistant message
- **THEN** each assistant message parent points to the user message for its turn

#### Scenario: Active head advances on completion
- **WHEN** a run completes with a visible assistant message
- **THEN** the conversation active head advances to that assistant message

### Requirement: User transcript is persisted before execution
The system SHALL persist the user message for a run before provider, graph, tool, or memory retrieval execution starts.

#### Scenario: Failed run keeps user message
- **WHEN** run execution fails after run creation
- **THEN** the transcript still includes the user message with its turn metadata
- **THEN** the failed assistant attempt is marked with error status when available

### Requirement: Visible assistant text is persisted from stream events
The system SHALL accumulate visible `text_delta` chunks into assistant transcript text for the active turn.

#### Scenario: Text deltas build assistant message
- **WHEN** a run streams multiple visible `text_delta` chunks
- **THEN** the assistant transcript message contains the concatenated visible answer text in event order

#### Scenario: Done marks assistant complete
- **WHEN** a run emits `done`
- **THEN** the assistant transcript message is marked completed

#### Scenario: Error marks assistant failed
- **WHEN** a run emits `error`
- **THEN** the assistant transcript message or turn is marked error with a bounded redacted error summary

### Requirement: Hidden thinking is excluded from visible transcript
The system SHALL NOT store `thinking_delta` content as visible assistant transcript text.

#### Scenario: Thinking stream is not answer history
- **WHEN** a run emits `thinking_delta` followed by `text_delta`
- **THEN** only the `text_delta` content is stored in visible assistant transcript parts
- **THEN** future conversation history ContextItems exclude the thinking content

### Requirement: Non-answer transcript parts are bounded
The system SHALL store tool, interrupt, resume, error, cancellation, and metadata transcript parts as bounded redacted summaries rather than unbounded raw payloads.

#### Scenario: Tool result becomes bounded summary
- **WHEN** a run emits a tool result or side-effect reuse event
- **THEN** the transcript stores a bounded tool summary part with tool name, status, and redacted preview
- **THEN** raw unbounded tool output is not stored in visible answer text

#### Scenario: HITL markers are persisted
- **WHEN** a run emits interrupt and resume events
- **THEN** the transcript stores bounded marker parts that identify the user-visible decision flow without raw runtime internals

### Requirement: Conversation APIs expose transcript safely
The system SHALL expose local conversation APIs for create, list, read, update metadata, and read transcript messages with pagination or bounded limits.

#### Scenario: List conversations
- **WHEN** a client requests conversations
- **THEN** the backend returns conversation summaries with ID, title, status, active head, latest turn time, archived flag, and no raw provider secrets

#### Scenario: Read transcript
- **WHEN** a client requests a conversation transcript
- **THEN** the backend returns ordered frontend-safe messages and parts for that conversation only

#### Scenario: Archive conversation
- **WHEN** a client archives a conversation
- **THEN** the conversation is excluded from the default active list
- **THEN** existing transcript rows are not deleted by default
