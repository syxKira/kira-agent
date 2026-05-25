## ADDED Requirements

### Requirement: Runtime actions are audited locally
The system SHALL persist redacted audit records for provider selection, run lifecycle, tool calls, controlled Python execution, project retrieval, skill activation, workflow execution, HITL interrupt/resume, memory operations, transcript writes, compaction, replacement handling, fork/rollback, cancellation, and export/inspection actions.

#### Scenario: Provider selection audit
- **WHEN** a run selects a real provider, request override, skill hint, configured default, or fixture fallback
- **THEN** an audit record SHALL capture provider/model/fallback decision metadata without raw API keys

#### Scenario: Transcript operation audit
- **WHEN** a conversation is compacted, forked, rolled back, archived, deleted, or used for context injection
- **THEN** an audit record SHALL capture conversation, turn, active head, source/target IDs, status, and redacted reason metadata

### Requirement: Audit export is read-only and redacted
The system SHALL expose bounded audit export APIs that return redacted audit records without replaying providers, tools, graph nodes, retrieval, memory extraction, or transcript mutation.

#### Scenario: Export audit records
- **WHEN** the frontend requests audit records for a thread, conversation, project root, memory ID, or time range
- **THEN** the response SHALL include matching records, pagination/limit metadata, and no raw secrets or hidden thinking

### Requirement: Audit writes are failure-tolerant
The system SHALL avoid failing the local web loop solely because a non-critical audit write fails, while surfacing a structured diagnostic.

#### Scenario: Audit insert fails
- **WHEN** the audit table insert fails during a provider or tool action
- **THEN** the action SHALL continue if its main operation is otherwise allowed and the doctor output SHALL report an audit storage diagnostic
