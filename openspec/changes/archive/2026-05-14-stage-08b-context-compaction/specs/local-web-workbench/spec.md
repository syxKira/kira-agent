## ADDED Requirements

### Requirement: Workbench exposes basic compaction controls
The workbench SHALL provide a minimal conversation compaction action in the existing side surface without requiring Stage 10 visual redesign.

#### Scenario: User triggers compaction
- **WHEN** the user selects a conversation and activates the compact action
- **THEN** the frontend calls the conversation compact API
- **THEN** the workbench refreshes transcript and context metadata for that conversation

#### Scenario: Compaction error is visible
- **WHEN** compaction fails
- **THEN** the frontend shows a bounded error state without exposing raw provider errors or secrets

### Requirement: Workbench shows compaction summaries in context inspector
The context inspector SHALL display `conversation_summary` and `compaction_summary` ContextItems with source IDs, stale status, summarizer metadata, trust label, and budget decisions.

#### Scenario: Inspector shows included summary
- **WHEN** a run context trace includes a compaction summary
- **THEN** the inspector displays the summary kind, summary ID, covered turn/message range, stale status, budget cost, and inclusion status

#### Scenario: Inspector shows stale or omitted summary
- **WHEN** a summary is stale or omitted from provider context
- **THEN** the inspector displays the stale or omission reason without showing raw hidden thinking or secrets

### Requirement: Workbench shows replacement stubs safely
The workbench SHALL display replacement stub metadata for tool-output replacements without exposing raw replaced output.

#### Scenario: Inspector shows replacement metadata
- **WHEN** a run context trace or transcript contains replacement metadata
- **THEN** the workbench displays replacement ID, reason, omitted count, source part ID, retention policy, and bounded summary
- **THEN** raw replacement content is not rendered

### Requirement: Transcript rendering distinguishes summaries from answers
The workbench SHALL render compaction and replacement metadata as transcript/context metadata rather than normal visible assistant answer text.

#### Scenario: Restored transcript excludes summary as answer
- **WHEN** a conversation transcript is restored after compaction
- **THEN** prior assistant answer text remains visible as answer text
- **THEN** compaction summaries and replacement stubs are visually or structurally distinct metadata rows
