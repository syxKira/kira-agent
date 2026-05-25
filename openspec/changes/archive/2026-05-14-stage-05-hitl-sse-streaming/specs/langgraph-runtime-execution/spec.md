## ADDED Requirements

### Requirement: Runtime supports graph interrupts

The graph runtime SHALL support LangGraph `interrupt` in skill-defined workflows and convert pending interrupts into Kira interrupt events.

#### Scenario: Workflow node pauses with interrupt

- **WHEN** a skill workflow node calls LangGraph `interrupt` with a valid Kira interrupt payload
- **THEN** runtime execution pauses at the checkpoint
- **THEN** the SSE stream emits a persisted `interrupt` event

#### Scenario: Interrupt does not require business nodes in core

- **WHEN** a skill declares arbitrary valid node names that may interrupt
- **THEN** Kira core handles the interrupt generically without hardcoded business workflow node names

### Requirement: Runtime resumes with Command resume

The graph runtime SHALL resume interrupted workflows using LangGraph `Command(resume=...)` and the existing checkpoint identity for the run.

#### Scenario: Resume value reaches interrupted node

- **WHEN** the client posts a valid resume value for the pending interrupt
- **THEN** the runtime invokes the graph with `Command(resume=...)` and the same `thread_id`
- **THEN** the interrupted node receives the resume value and graph execution continues

#### Scenario: Terminal run cannot resume

- **WHEN** a run is already completed, failed terminally, or cancelled
- **THEN** runtime resume returns a structured conflict or validation error instead of invoking graph work

### Requirement: Runtime uses Stage 04 reliability during HITL

The graph runtime SHALL use Stage 04 run locks, checkpoints, event persistence, retry classification, and side-effect ledger behavior during HITL execution and resume.

#### Scenario: Completed side effect is reused after resume

- **WHEN** a graph resumes after an interrupt and reaches a previously completed side-effect-capable tool call
- **THEN** the runtime reuses the completed ledger result rather than executing the side effect again

#### Scenario: Unknown side effect blocks automatic resume

- **WHEN** a resume would cross a side-effect ledger entry with unknown status
- **THEN** the runtime emits a structured repair-required error instead of automatically continuing
