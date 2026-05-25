## ADDED Requirements

### Requirement: Conversation context uses summaries plus recent raw tail
The system SHALL prefer the latest non-stale compaction summary for older active-chain transcript spans and append recent visible raw user/assistant messages after the summary tail boundary.

#### Scenario: Summary replaces older raw context
- **WHEN** a conversation has a non-stale compaction summary covering older active-chain messages
- **THEN** the context builder emits summary ContextItems for the covered span
- **THEN** it does not also inject the same covered raw messages as conversation history

#### Scenario: Recent tail remains raw
- **WHEN** a compaction summary defines `tail_start_message_id`
- **THEN** active-chain messages at or after the tail boundary remain eligible as raw `conversation_history` ContextItems
- **THEN** older covered messages are represented by the summary within budget

### Requirement: Stale summaries are omitted from provider context
The system SHALL omit stale compaction summaries from provider input unless they are refreshed or explicitly marked safe for read-only inspection.

#### Scenario: Stale summary is traced
- **WHEN** a compaction summary is stale during context building
- **THEN** provider input excludes the stale summary
- **THEN** the context trace records the summary ID, stale reason, source range, and omission reason

### Requirement: Replacement stubs participate in transcript context
The system SHALL include bounded replacement stubs or tool summaries from the active chain when they are relevant and within context budget.

#### Scenario: Replacement stub included
- **WHEN** a prior tool output has a replacement record and is selected for context
- **THEN** the context builder emits bounded replacement summary text
- **THEN** raw replaced output is not included in provider input

#### Scenario: Replacement omitted by budget
- **WHEN** replacement stubs exceed context budget
- **THEN** the context trace records omitted replacement IDs, source message/part IDs, budget costs, and omission reasons

### Requirement: Transcript context trace covers compaction decisions
The system SHALL record included, truncated, omitted, stale, and refreshed transcript context decisions for summaries, raw messages, tool summaries, and replacement stubs.

#### Scenario: Mixed transcript context trace
- **WHEN** a run uses a compaction summary, recent conversation history, and a replacement stub
- **THEN** the run context trace identifies each item kind separately
- **THEN** the trace includes conversation ID, turn IDs, message IDs, part IDs, summary IDs, replacement IDs, trust labels, budget costs, and reasons
