# conversation-history-context Specification

## Purpose
TBD - created by archiving change stage-08a-transcript-core. Update Purpose after archive.
## Requirements
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

### Requirement: Inactive branch messages are omitted from provider context
The system SHALL exclude messages outside the selected conversation active parent chain from provider input after fork or rollback.

#### Scenario: Rolled-back future is omitted
- **WHEN** a conversation is rolled back before later messages and a new run is created
- **THEN** provider input excludes the abandoned later messages
- **THEN** the context trace records those messages as inactive branch omissions when relevant

#### Scenario: Fork source future is omitted
- **WHEN** a forked conversation creates a run after the source conversation continues independently
- **THEN** provider input for the fork excludes source conversation messages after the fork point
- **THEN** the fork context trace identifies the fork source boundary

### Requirement: Compaction summaries respect active branch
The system SHALL include only compaction summaries that are valid for the selected conversation active parent chain and SHALL omit summaries that cover inactive branch-only messages.

#### Scenario: Rollback invalidates covered future summary
- **WHEN** a compaction summary covers messages that become inactive after rollback
- **THEN** the context builder omits that summary or marks it stale for the current active branch
- **THEN** the context trace records the summary ID and inactive-branch reason

### Requirement: Branch context trace is inspectable
The system SHALL record active-head, fork source, rollback transition, included active-chain items, and omitted inactive branch items in transcript context traces.

#### Scenario: Trace explains branch decision
- **WHEN** a run is created after rollback
- **THEN** the run context trace includes current active head ID, rollback transition ID when available, included active-chain item IDs, and omitted inactive branch message IDs

