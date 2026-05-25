## ADDED Requirements

### Requirement: Run state includes conversation linkage
The run state projection endpoint SHALL include frontend-safe `conversation_id`, `turn_id`, and transcript message linkage when a run belongs to a conversation.

#### Scenario: State shows conversation link
- **WHEN** a client requests state for a conversation-backed run
- **THEN** the state response includes `conversation_id`, `turn_id`, user message ID, assistant message ID when available, and no raw provider secrets

### Requirement: Replay includes transcript summaries without side effects
The replay/debug export SHALL include saved conversation and transcript linkage for a run and SHALL NOT rebuild transcript context or append transcript parts.

#### Scenario: Replay is read-only for transcript
- **WHEN** replay/debug export is requested for a conversation-backed run
- **THEN** the export reads persisted conversation/turn/message references
- **THEN** no new transcript message, transcript part, context trace, provider call, tool call, memory record, or retrieval trace is created

### Requirement: SSE reconnect does not duplicate transcript text
The system SHALL avoid appending duplicate assistant transcript text when a client reconnects to read persisted SSE events.

#### Scenario: Reconnect replays events read-only
- **WHEN** a client reconnects to an existing event stream with `after_seq`
- **THEN** replayed persisted events are streamed to the client
- **THEN** replayed events do not append duplicate transcript parts
