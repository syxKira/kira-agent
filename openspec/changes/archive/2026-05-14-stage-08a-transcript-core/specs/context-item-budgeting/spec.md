## ADDED Requirements

### Requirement: Conversation ContextItems are supported
The system SHALL represent transcript-derived context as typed ContextItems with stable IDs, text, metadata, trust label, citations or transcript references, and estimated budget cost.

#### Scenario: User transcript becomes ContextItem
- **WHEN** the context builder selects a prior visible user message
- **THEN** it emits a `conversation_history` ContextItem with conversation ID, turn ID, message ID, role, trust label, and budget cost

#### Scenario: Tool summary becomes ContextItem
- **WHEN** the context builder selects a prior bounded tool summary
- **THEN** it emits a `tool_summary` ContextItem with tool name, status, source message/part IDs, and budget cost

### Requirement: Conversation ContextItems are packed with other context
The system SHALL pack conversation history alongside skill, project, and memory ContextItems using deterministic priority and budget rules.

#### Scenario: Mixed context trace
- **WHEN** a run uses conversation history, project retrieval, and memory retrieval
- **THEN** the context trace identifies each ContextItem kind separately
- **THEN** omission and truncation records preserve the source kind and IDs

### Requirement: Transcript omission metadata is inspectable
The system SHALL record why transcript ContextItems were included, truncated, or omitted.

#### Scenario: Old history is omitted
- **WHEN** the context budget cannot include all eligible transcript messages
- **THEN** the trace records omitted message IDs, turn IDs, item kind, reason, and estimated budget cost
