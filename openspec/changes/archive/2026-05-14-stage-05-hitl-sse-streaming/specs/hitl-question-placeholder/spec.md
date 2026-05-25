## MODIFIED Requirements

### Requirement: Provide ask user question placeholder

The system SHALL provide `ask_user_question` as a structured tool that can request human input through the Stage 05 interrupt/resume flow when invoked inside a checkpointed graph run, while preserving structured non-interactive validation behavior for unsupported contexts.

#### Scenario: Question request emits interrupt in graph run

- **WHEN** `ask_user_question` is invoked with a prompt and optional fields during a checkpointed graph run
- **THEN** the run persists and streams an `interrupt` event with `kind: "question"`, stable question ID metadata, and declared response constraints
- **THEN** tool execution waits for a validated resume value instead of returning an immediate completed placeholder

#### Scenario: Unsupported non-graph question remains structured

- **WHEN** `ask_user_question` is invoked outside an interrupt-capable graph context
- **THEN** it returns a structured `ToolResult` explaining that interactive resume is unavailable in that context

### Requirement: Validate question payloads

The system SHALL validate question text and optional response field definitions before creating a question interrupt or returning a structured validation error.

#### Scenario: Invalid question is rejected

- **WHEN** `ask_user_question` is invoked without meaningful question text
- **THEN** it returns or emits a structured validation error in the `ToolResult` or Kira event envelope
- **THEN** the run does not wait on an invalid human prompt

## REMOVED Requirements

### Requirement: Defer interrupt and resume behavior

**Reason**: Stage 05 implements the interrupt/resume behavior that Stage 02 intentionally deferred.

**Migration**: Use the Stage 05 `interrupt` event and `POST /api/runs/{thread_id}/resume` flow for graph-based `ask_user_question` interactions.
