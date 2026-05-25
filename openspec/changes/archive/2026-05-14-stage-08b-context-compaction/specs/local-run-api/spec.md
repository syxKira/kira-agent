## ADDED Requirements

### Requirement: Conversation compact API is available
The system SHALL expose a local API endpoint for creating or refreshing compaction summaries for an existing active conversation.

#### Scenario: Compact conversation
- **WHEN** a client posts to `POST /api/conversations/{conversation_id}/compact`
- **THEN** the backend creates or refreshes a compaction summary for eligible active-chain messages
- **THEN** the response includes frontend-safe summary ID, status, source range, tail boundary, stale status, summarizer metadata, token estimates, and omission metadata

#### Scenario: Unknown or archived conversation cannot compact
- **WHEN** a client requests compaction for an unknown or archived conversation
- **THEN** the backend returns a structured not-found or validation error
- **THEN** no provider call, summary record, transcript part, replacement record, memory record, or tool call is created

### Requirement: Conversation context API exposes compaction and replacement decisions
The conversation context API SHALL return frontend-safe summary and replacement metadata for transcript ContextItems eligible for the next run.

#### Scenario: Context endpoint includes summary and replacement metadata
- **WHEN** a client requests `GET /api/conversations/{conversation_id}/context`
- **THEN** the response includes eligible `conversation_summary`, `compaction_summary`, `conversation_history`, and `tool_summary` items
- **THEN** replacement IDs, summary IDs, stale reasons, and budget estimates are visible without raw replaced output

### Requirement: Run creation may trigger explicit overflow compaction
The run creation API SHALL optionally create or refresh compaction summaries when selected conversation history would exceed configured transcript thresholds.

#### Scenario: Overflow compaction occurs before provider input
- **WHEN** a run is created in a long conversation and transcript context exceeds configured thresholds
- **THEN** the backend creates or refreshes an explicit compaction summary before final provider input assembly
- **THEN** the run context trace records the summary and any omitted raw messages

#### Scenario: Overflow compaction fallback is non-fatal
- **WHEN** overflow compaction fails
- **THEN** run creation falls back to bounded Stage 08a recent-history behavior when possible
- **THEN** the run context trace records a structured compaction failure without raw secrets

### Requirement: Run context trace exposes summary and replacement usage
The run context trace API SHALL show included, truncated, omitted, and stale compaction summaries and tool-output replacement stubs.

#### Scenario: Trace returns Stage 08b transcript items
- **WHEN** a run uses compaction summaries or replacement stubs
- **THEN** the context trace includes item kind, summary IDs, replacement IDs, source message/part IDs, stale status, trust labels, budget costs, and omission reasons
