## ADDED Requirements

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
