## ADDED Requirements

### Requirement: Conversation context uses active parent chain
The system SHALL build transcript context from the selected conversation's active parent message chain rather than every message ordered by timestamp.

#### Scenario: Active chain is selected
- **WHEN** a run is created with a `conversation_id`
- **THEN** the context builder walks the conversation active head parent chain
- **THEN** only messages on that chain are eligible for conversation history injection

#### Scenario: Missing conversation has no transcript context
- **WHEN** a run is created without a valid existing conversation
- **THEN** the backend creates or rejects according to run API rules
- **THEN** it does not inject transcript from any unrelated conversation

### Requirement: Recent visible turns become ContextItems
The system SHALL convert recent visible user and assistant transcript messages into bounded `conversation_history` ContextItems.

#### Scenario: Follow-up sees previous user turn
- **WHEN** a user sends "hello" in a conversation and then sends "what did I just say" in the same conversation
- **THEN** the second run receives a `conversation_history` ContextItem containing the prior visible user turn

#### Scenario: Assistant answer is included
- **WHEN** a prior assistant response completed in the same active chain
- **THEN** eligible visible assistant text may be included as conversation history within budget

### Requirement: Conversation context is budgeted and traced
The system SHALL pack conversation history through the ContextItem budget path and SHALL record included, truncated, and omitted transcript items.

#### Scenario: History exceeds budget
- **WHEN** eligible transcript history exceeds the configured context budget
- **THEN** lower-priority or older transcript items are omitted or truncated
- **THEN** the run context trace records message IDs, turn IDs, reasons, and budget costs for included and omitted transcript context

### Requirement: Conversation context is isolated
The system SHALL prevent transcript history from one conversation from being injected into another conversation.

#### Scenario: Separate conversations do not share transcript
- **WHEN** conversation A contains a prior user message and conversation B creates a run
- **THEN** conversation B's context trace does not include conversation A message IDs or text

### Requirement: Hidden thinking is never conversation history
The system SHALL exclude provider reasoning, hidden thinking, and `thinking_delta` text from conversation history ContextItems.

#### Scenario: Thinking is omitted from context
- **WHEN** a previous run emitted thinking content and visible answer content
- **THEN** follow-up context may include visible answer content
- **THEN** follow-up context does not include thinking content

### Requirement: Tool summaries are bounded context
The system SHALL represent prior relevant tool outputs as bounded `tool_summary` ContextItems or transcript summary parts, not raw unbounded payloads.

#### Scenario: Prior tool output is summarized
- **WHEN** a previous turn produced a large tool result
- **THEN** follow-up context includes at most a bounded tool summary with tool name, status, and redacted preview
- **THEN** raw large output is omitted from provider input

### Requirement: Transcript is distinct from memory
The system SHALL keep transcript context separate from Stage 07 memory records and SHALL NOT automatically promote transcript messages into memory.

#### Scenario: Transcript does not create memory
- **WHEN** a conversation run completes with user and assistant transcript messages
- **THEN** no memory record is created unless an explicit Stage 07 memory write or candidate approval occurs
