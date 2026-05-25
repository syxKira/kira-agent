## ADDED Requirements

### Requirement: Workbench keeps selected conversation
The workbench SHALL create or select a conversation and SHALL pass its `conversation_id` on follow-up runs.

#### Scenario: First prompt creates selected conversation
- **WHEN** the user submits a prompt with no selected conversation
- **THEN** the frontend uses the returned `conversation_id` as the selected conversation

#### Scenario: Follow-up reuses conversation
- **WHEN** the user submits a second prompt after a run completed
- **THEN** the frontend sends the selected `conversation_id` in the run creation request

### Requirement: Workbench renders prior transcript
The workbench SHALL load and render prior visible transcript messages for the selected conversation before and alongside the current stream.

#### Scenario: Transcript restores after refresh
- **WHEN** the frontend loads with a selected conversation or user selects one from the conversation list
- **THEN** it fetches the transcript and renders prior visible user and assistant messages without requiring SSE replay

#### Scenario: Hidden thinking is not transcript UI
- **WHEN** a previous run emitted `thinking_delta`
- **THEN** the transcript view does not render that thinking content as assistant answer text

### Requirement: Conversation list is available in the workbench
The workbench SHALL provide a functional conversation list/create/select surface without requiring Stage 10 visual redesign.

#### Scenario: User switches conversations
- **WHEN** the user selects a different active conversation
- **THEN** the workbench loads that conversation's transcript
- **THEN** the next run uses that conversation ID

### Requirement: Context inspector shows transcript context
The workbench context inspector SHALL show conversation history and tool summary ContextItems when they are included or omitted for a run.

#### Scenario: Inspector shows history inclusion
- **WHEN** a run includes conversation history ContextItems
- **THEN** the context inspector displays their kind, role, turn/message IDs, trust label, budget cost, and omission/truncation status when applicable
