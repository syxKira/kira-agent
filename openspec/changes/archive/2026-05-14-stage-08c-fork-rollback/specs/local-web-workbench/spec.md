## ADDED Requirements

### Requirement: Workbench exposes basic fork controls
The workbench SHALL provide a minimal control to fork a selected conversation from a visible transcript message or turn without requiring Stage 10 visual redesign.

#### Scenario: User forks from transcript message
- **WHEN** the user selects a valid transcript message and activates fork
- **THEN** the frontend calls the fork API
- **THEN** the new conversation becomes selectable and its transcript/context reflects the fork point

### Requirement: Workbench exposes basic rollback controls
The workbench SHALL provide a minimal control to roll back a conversation active head to a selected active-chain message or turn.

#### Scenario: User rolls back conversation
- **WHEN** the user selects a valid active-chain message and activates rollback
- **THEN** the frontend calls the rollback API
- **THEN** the conversation transcript and context metadata refresh to show the new active head and inactive branch metadata

### Requirement: Workbench shows branch and active-head metadata
The workbench SHALL display active head, fork source, rollback transition, and inactive branch omission metadata in existing conversation, transcript, or context inspector surfaces.

#### Scenario: Inspector shows inactive branch omission
- **WHEN** run context omits messages because they are outside the active branch
- **THEN** the context inspector displays the branch omission reason, message IDs, turn IDs, and active head metadata without raw secrets

### Requirement: Workbench shows resume conflicts
The workbench SHALL render structured resume conflict responses when a user attempts to resume an interrupted run outside the active branch.

#### Scenario: Resume conflict displayed
- **WHEN** resume returns an inactive-branch conflict
- **THEN** the frontend shows a bounded conflict state with thread ID, turn ID, active head ID, and suggested next action metadata
- **THEN** raw hidden thinking and provider secrets are not rendered
