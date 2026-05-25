## ADDED Requirements

### Requirement: HITL supports memory approval prompts
The frontend SHALL reuse the Stage 05 HITL approval/edit UI for memory write and promotion approvals when backend policy requires human approval.

#### Scenario: Memory promotion approval is shown
- **WHEN** the backend emits an interrupt for memory promotion approval
- **THEN** the frontend shows a focused approval panel with memory summary, target scope, approve/reject actions, and redacted metadata

#### Scenario: Memory candidate edit is shown
- **WHEN** the backend emits an edit interrupt for a memory extraction candidate
- **THEN** the frontend lets the user edit the candidate text before submitting the resume decision

### Requirement: Memory approval resume is persisted
The frontend SHALL submit memory approval decisions through the existing resume endpoint and render resume markers as normal timeline events.

#### Scenario: Approved memory write resumes run
- **WHEN** the user approves a pending memory approval interrupt
- **THEN** the frontend posts the matching `interrupt_id` and decision to the resume endpoint
- **THEN** the timeline receives a persisted resume marker and subsequent memory outcome events or summaries
