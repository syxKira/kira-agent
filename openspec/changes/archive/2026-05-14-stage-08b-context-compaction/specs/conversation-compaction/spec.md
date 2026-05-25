## ADDED Requirements

### Requirement: Compaction summaries are explicit transcript artifacts
The system SHALL represent conversation compaction as explicit records linked to a conversation, source message range, source turn range, summary text, tail boundary, source hash, token estimates, summarizer metadata, status, and timestamps.

#### Scenario: Manual compaction creates summary record
- **WHEN** a client requests compaction for an active conversation
- **THEN** the backend creates a compaction summary record instead of rewriting or deleting source transcript messages
- **THEN** the record includes covered message IDs, covered turn IDs, `tail_start_message_id`, source hash, estimated before/after budget cost, summarizer metadata, and status

#### Scenario: Source messages remain inspectable
- **WHEN** a compaction summary covers older transcript messages
- **THEN** the original transcript messages and parts remain readable from transcript APIs
- **THEN** the summary is an additional transcript/context artifact, not a replacement for stored history

### Requirement: Compaction uses deterministic fixture summarization by default
The system SHALL provide a deterministic fixture summarizer for tests and local runs without a valid real provider key, while allowing an optional real-provider summarizer through the existing redacted provider layer.

#### Scenario: No real provider key uses fixture summarizer
- **WHEN** compaction is requested and no valid real provider key is available
- **THEN** compaction succeeds with fixture summarizer metadata
- **THEN** no test or local run requires a real API key by default

#### Scenario: Real provider summarizer is redacted
- **WHEN** compaction uses a configured real provider summarizer
- **THEN** summary metadata may include provider profile and model
- **THEN** raw API keys, provider config secrets, hidden thinking, and raw provider errors are absent from stored summaries, traces, logs, and frontend responses

### Requirement: Compaction summaries preserve conversation facts
The system SHALL summarize older active-chain transcript spans while preserving user goals, constraints, decisions, unresolved questions, selected skills, project root context, relevant bounded tool outcomes, and source references.

#### Scenario: Summary preserves decisions and open questions
- **WHEN** a covered span contains user constraints, assistant decisions, and unresolved questions
- **THEN** the compaction summary includes those points in bounded text
- **THEN** the summary cites the covered message and turn range

#### Scenario: Summary excludes unsafe content
- **WHEN** a covered span contains hidden thinking, API keys, authorization headers, cookies, raw provider config, or unbounded raw tool output
- **THEN** the summary excludes or redacts that content
- **THEN** the summary records bounded omission metadata when relevant

### Requirement: Compaction summaries become stale when sources change
The system SHALL mark or treat a compaction summary as stale when covered transcript messages, covered transcript parts, or referenced replacement records no longer match the stored source hash or status.

#### Scenario: Covered message changes after compaction
- **WHEN** a transcript message covered by a compaction summary is edited, replaced, archived, or otherwise invalidated
- **THEN** the existing compaction summary is marked stale or omitted as stale during context building
- **THEN** the stale reason is visible in the conversation context trace

#### Scenario: Refresh creates a new summary
- **WHEN** a client refreshes a stale compaction summary
- **THEN** the backend creates a refreshed summary linked to the previous summary ID
- **THEN** source messages remain intact and older stale summaries remain inspectable

### Requirement: Overflow-triggered compaction is explicit
The system SHALL create explicit compaction records when transcript context would exceed configured raw-history thresholds and overflow compaction is enabled.

#### Scenario: Long conversation overflows raw history threshold
- **WHEN** a new run in a conversation would exceed configured transcript history thresholds
- **THEN** the backend creates or refreshes a compaction summary for older active-chain messages before final provider input assembly
- **THEN** the run context trace records the compaction summary and any fallback or omission decisions

#### Scenario: Compaction failure falls back safely
- **WHEN** overflow-triggered compaction fails
- **THEN** the run does not lose existing transcript messages
- **THEN** provider input falls back to bounded recent-history behavior
- **THEN** the context trace records a structured compaction error without raw provider secrets

### Requirement: Compaction does not create memory records automatically
The system SHALL keep compaction summaries conversation-scoped and SHALL NOT automatically create Stage 07 memory records from compaction output.

#### Scenario: Summary completion does not write memory
- **WHEN** a compaction summary is created or refreshed
- **THEN** no memory record is created unless a separate Stage 07 memory candidate approval or explicit memory write occurs
