## ADDED Requirements

### Requirement: Large or sensitive tool output is replaced by bounded stubs
The system SHALL replace oversized or sensitive tool output in transcript context with a bounded model-visible summary or stub rather than injecting raw unbounded output.

#### Scenario: Oversized tool output is replaced
- **WHEN** a tool result exceeds configured transcript or context limits
- **THEN** the backend creates a tool-output replacement record
- **THEN** transcript and provider context receive a bounded stub or summary instead of raw output

#### Scenario: Sensitive tool output is replaced
- **WHEN** a tool result contains API keys, bearer tokens, cookies, private keys, raw provider config, or other guarded secrets
- **THEN** the replacement summary redacts the sensitive content
- **THEN** the raw sensitive content is absent from provider input, frontend responses, context traces, state, replay, and diagnostics

### Requirement: Replacement records preserve provenance metadata
The system SHALL store frontend-safe replacement metadata including replacement ID, source conversation ID, turn ID, thread ID, message ID, part ID, tool name, output hash, summary, omitted character count, reason, retention policy, status, and timestamps.

#### Scenario: Replacement metadata is queryable
- **WHEN** a transcript part is replaced
- **THEN** the replacement record can be resolved by replacement ID for summary metadata
- **THEN** the metadata includes source IDs and output hash without exposing raw sensitive content

#### Scenario: Replacement reasons are explicit
- **WHEN** replacement is created
- **THEN** the reason is one of the supported replacement reasons such as `too_large`, `secret_guard`, `manual_clear`, or `compaction_prune`
- **THEN** the retention policy is one of the supported policies such as `none`, `debug_only`, or `local_blob`

### Requirement: Provider input uses replacement stubs only
The system SHALL inject only bounded replacement summaries or tool summaries into provider input and SHALL NOT inject raw replaced output.

#### Scenario: Follow-up uses replacement stub
- **WHEN** a follow-up run needs context from a prior replaced tool output
- **THEN** the context builder emits a bounded `tool_summary` ContextItem or replacement stub ContextItem
- **THEN** the raw replaced output is omitted from provider input

#### Scenario: Context trace explains replacement
- **WHEN** a replacement stub is included, truncated, or omitted from a run
- **THEN** the run context trace records the replacement ID, source part ID, reason, budget cost, and inclusion decision

### Requirement: Replacement storage is local and redacted
The system SHALL keep replacement storage Kira-owned and local, and SHALL expose only redacted frontend-safe metadata in Stage 08b APIs.

#### Scenario: Retained local blob is not exposed by default
- **WHEN** a replacement record has retention policy `local_blob` or `debug_only`
- **THEN** Stage 08b frontend APIs expose only the summary, hash, omitted count, reason, status, and redacted reference metadata
- **THEN** raw blob resolution is not available without future Stage 09 policy

#### Scenario: Replay does not resolve raw replacement
- **WHEN** replay/debug export includes a run with replacement records
- **THEN** replay includes saved replacement summaries and metadata only
- **THEN** replay does not read raw replacement blobs, call tools, call providers, or create transcript parts

### Requirement: Replacement records can affect summary freshness
The system SHALL invalidate or mark compaction summaries stale when a replacement record referenced by the summary changes status, summary text, hash, or retention metadata.

#### Scenario: Replacement refresh stales summary
- **WHEN** a replacement record included in a compaction source span is refreshed or invalidated
- **THEN** any compaction summary depending on that replacement is marked stale or omitted as stale
- **THEN** context traces expose the stale dependency reason
