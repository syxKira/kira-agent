## ADDED Requirements

### Requirement: Run state includes branch metadata
The run state projection endpoint SHALL include frontend-safe branch metadata when a run belongs to a forked or rolled-back conversation.

#### Scenario: State shows branch context
- **WHEN** a client requests state for a run after fork or rollback
- **THEN** the response includes conversation ID, turn ID, active head ID at run creation, fork source or rollback transition metadata when available, and no raw provider secrets

### Requirement: Replay is read-only for branch state
The replay/debug export SHALL include saved fork/rollback and active-head metadata without mutating conversation active head, creating branch records, or rebuilding transcript context.

#### Scenario: Replay does not change active head
- **WHEN** replay/debug export is requested for a branch-aware run
- **THEN** replay reads saved branch metadata
- **THEN** replay does not update active head, create transcript parts, create branch records, call providers, call tools, or create memory records

### Requirement: Replay preserves historical branch decision
The replay/debug export SHALL report active-head and inactive-branch context decisions as observed by the run.

#### Scenario: Replay uses saved run branch view
- **WHEN** a conversation active head changes after a completed run
- **THEN** replay for the completed run still shows the active head and context decisions saved for that run
- **THEN** replay does not rebuild context using the current active head
