## ADDED Requirements

### Requirement: Summary ContextItems are supported
The system SHALL represent transcript summaries as typed `conversation_summary` and `compaction_summary` ContextItems with stable IDs, bounded text, metadata, trust label, transcript references, and estimated budget cost.

#### Scenario: Compaction summary becomes ContextItem
- **WHEN** the context builder selects a non-stale compaction summary
- **THEN** it emits a `compaction_summary` ContextItem with conversation ID, summary ID, source message range, source turn range, tail boundary, stale status, trust label, and budget cost

#### Scenario: Conversation summary becomes ContextItem
- **WHEN** the context builder selects a rolling conversation summary
- **THEN** it emits a `conversation_summary` ContextItem with summary ID, covered source IDs, summarizer metadata, trust label, and budget cost

### Requirement: Summary ContextItems have deterministic budget priority
The system SHALL pack compaction and conversation summary ContextItems with deterministic priority relative to recent conversation history, tool summaries, project context, memory, and skill context.

#### Scenario: Summary preserves older context under budget
- **WHEN** a conversation has old summarized history and recent raw tail messages
- **THEN** the budget packer can include the summary before lower-value old raw messages
- **THEN** inclusion and omission decisions are stable for identical inputs

### Requirement: Replacement metadata is traceable in budget decisions
The system SHALL record replacement stub budget decisions with replacement IDs, source part IDs, reasons, omitted counts, and budget costs.

#### Scenario: Replacement stub is truncated
- **WHEN** a replacement stub text exceeds per-item budget
- **THEN** the context packer truncates or omits it according to budget rules
- **THEN** the trace records replacement ID, truncation or omission reason, and budget cost

### Requirement: Shared schemas include summary and replacement context
The system SHALL publish shared schemas for compaction summaries, replacement records, summary ContextItems, replacement trace metadata, and Stage 08b examples.

#### Scenario: Frontend validates summary trace
- **WHEN** the frontend fetches a run context trace containing compaction and replacement metadata
- **THEN** the payload validates against shared schemas
- **THEN** the frontend can render item kind, source IDs, stale status, replacement reason, and budget metadata without raw secrets
