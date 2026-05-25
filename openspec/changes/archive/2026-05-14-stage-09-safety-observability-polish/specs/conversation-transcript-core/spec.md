## ADDED Requirements

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
