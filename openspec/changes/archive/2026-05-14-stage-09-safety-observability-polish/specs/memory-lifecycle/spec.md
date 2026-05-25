## ADDED Requirements

### Requirement: Memory writes and lifecycle actions are permission-aware
Memory creation, extraction candidate approval, archive, stale, refresh, promote, merge, delete, and project/user scope writes SHALL evaluate permission decisions before mutation.

#### Scenario: Project or user memory write
- **WHEN** a memory write targets `project` or `user` scope
- **THEN** the system SHALL ask or reject according to policy unless explicitly allowed, and SHALL persist a redacted audit record

### Requirement: Memory audit and trace output remain redacted
Memory retrieval, citation creation, extraction candidates, guard decisions, and lifecycle events SHALL appear in audit and trace export without rejected raw secret text or raw provider config.

#### Scenario: Candidate rejected by secret guard
- **WHEN** extraction text contains a raw API key
- **THEN** memory candidates, audit records, trace export, and frontend responses SHALL omit the raw key and include redacted guard reasons
