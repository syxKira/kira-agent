## ADDED Requirements

### Requirement: Memory lifecycle actions are explicit
The system SHALL expose lifecycle actions for explain, archive, delete, merge, refresh, stale, and promote.

#### Scenario: Archive stops injection
- **WHEN** a user archives a memory
- **THEN** the memory status becomes `archived` and the memory is excluded from default retrieval and injection

#### Scenario: Delete leaves tombstone
- **WHEN** a user deletes a memory
- **THEN** the memory is removed from injectable records and a tombstone is stored with redacted deletion metadata

### Requirement: Merge preserves provenance
The system SHALL merge duplicate memories while preserving source metadata, citations, prior IDs, and lifecycle events.

#### Scenario: Merge duplicate memories
- **WHEN** a user merges two memory records
- **THEN** one active memory remains, merged IDs are recorded, source/citation metadata is preserved, and duplicate records are not injected

### Requirement: Refresh updates confidence and source
The system SHALL refresh a memory with new evidence by updating confidence, source summaries, tags, and last-reviewed metadata without losing prior provenance.

#### Scenario: Refresh records new evidence
- **WHEN** a memory is refreshed with valid evidence
- **THEN** the memory metadata is updated and a refresh event records the redacted evidence summary

### Requirement: Promotion obeys approval policy
The system SHALL require approval before promoting memory to broader `project` or `user` scope unless local policy explicitly permits the action.

#### Scenario: Promote requires approval
- **WHEN** a user or extraction flow promotes `projectLocal` memory to `project` or `user` scope without an existing approval
- **THEN** the backend returns or emits an approval requirement and does not promote the memory yet

#### Scenario: Approved promotion succeeds
- **WHEN** a valid HITL approval or explicit policy approval is supplied
- **THEN** the memory scope is updated, a promote event is recorded, and public payloads remain redacted

### Requirement: Lifecycle actions validate secret safety
The system SHALL run secret/sensitive guard for lifecycle actions that change memory text, source, scope, or evidence.

#### Scenario: Unsafe refresh is rejected
- **WHEN** a refresh or merge action introduces secret-like text
- **THEN** the backend rejects the action and persists no unsafe memory content
