# conversation-transcript-core Specification

## Purpose
TBD - created by archiving change stage-08a-transcript-core. Update Purpose after archive.
## Requirements
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

### Requirement: Transcript stores compaction parts safely
The system SHALL store compaction summary transcript artifacts as bounded, redacted, non-answer parts or system messages without changing visible assistant answer text.

#### Scenario: Compaction appears in transcript metadata
- **WHEN** a conversation is compacted
- **THEN** the transcript can expose a frontend-safe compaction artifact with summary text, source range, status, and timestamps
- **THEN** it does not appear as if the assistant visibly answered with that summary

### Requirement: Transcript stores replacement parts safely
The system SHALL store tool-output replacement transcript artifacts as bounded, redacted summary or stub parts linked to the source tool result.

#### Scenario: Replacement part is not visible assistant answer
- **WHEN** a tool output is replaced
- **THEN** the transcript stores a replacement or tool summary part with replacement metadata
- **THEN** restored assistant answer text excludes raw replaced output and excludes replacement internals

### Requirement: Transcript APIs expose summary and replacement metadata
The system SHALL expose frontend-safe compaction and replacement metadata through transcript APIs without exposing raw provider secrets, hidden thinking, or raw replacement blobs.

#### Scenario: Transcript includes compaction metadata
- **WHEN** a client reads a conversation transcript after compaction
- **THEN** the response includes summary IDs, source ranges, stale status, and bounded summary text
- **THEN** the response does not include raw hidden thinking or provider secrets

#### Scenario: Transcript includes replacement metadata
- **WHEN** a client reads a conversation transcript with replaced tool output
- **THEN** the response includes replacement ID, reason, omitted count, hash or hash prefix, retention policy, and bounded summary
- **THEN** raw replaced content is not exposed

### Requirement: Transcript stores fork markers safely
The system SHALL store fork provenance as frontend-safe transcript metadata or marker parts without changing visible assistant answer text.

#### Scenario: Fork marker is recorded
- **WHEN** a conversation is forked from a source message
- **THEN** the source conversation and forked conversation expose bounded fork metadata with source conversation ID, source message ID, source turn ID when available, and created fork conversation ID
- **THEN** the marker does not appear as normal assistant answer text

### Requirement: Transcript stores rollback markers safely
The system SHALL store rollback metadata or marker parts when active head moves backward without deleting or rewriting source messages.

#### Scenario: Rollback marker is recorded
- **WHEN** a conversation is rolled back
- **THEN** transcript APIs expose bounded rollback metadata with previous active head, new active head, affected turn/message IDs when available, and timestamp
- **THEN** original transcript messages remain readable

### Requirement: Transcript APIs distinguish active and inactive messages
The system SHALL expose enough frontend-safe branch metadata for clients to distinguish active-chain messages from inactive branch messages after fork or rollback.

#### Scenario: Read transcript after rollback
- **WHEN** a client reads a conversation transcript after rollback and new follow-up messages
- **THEN** the response includes active-chain and inactive branch metadata
- **THEN** hidden thinking and raw provider secrets remain excluded

### Requirement: Transcript operations are audited
Transcript writes, assistant text persistence, error markers, HITL markers, compaction, replacement creation/inspection, archive/delete, fork/rollback, and context injection SHALL write redacted audit records with conversation, turn, thread, active head, and operation metadata.

#### Scenario: Context injection audit
- **WHEN** conversation history is injected into provider context
- **THEN** audit and trace export SHALL list included active-chain items, omitted inactive items, compaction summaries, replacement stubs, and branch metadata without hidden thinking

### Requirement: Transcript deletion is explicit and audited
Conversation archive/delete or transcript content deletion SHALL require an explicit user action, SHALL preserve audit tombstone metadata, and SHALL NOT occur as part of rollback, compaction, memory extraction, trace export, or replay.

#### Scenario: Rollback does not delete content
- **WHEN** a conversation is rolled back
- **THEN** abandoned future messages SHALL remain stored as inactive branch content and audit SHALL record the rollback without deleting transcript rows

### Requirement: Replacement inspection is gated and redacted
Retained replacement output inspection SHALL require an allowed retention policy and a Stage 09 permission decision, and responses SHALL redact sensitive content before display/export.

#### Scenario: Inspect retained replacement
- **WHEN** a user requests retained replacement output
- **THEN** the response SHALL include redacted content or a policy denial, plus hash/reference/reason metadata and an audit record ID

