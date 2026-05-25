# hitl-interrupt-resume Specification

## Purpose
TBD - created by archiving change stage-05-hitl-sse-streaming. Update Purpose after archive.
## Requirements
### Requirement: Interrupt payloads are typed and redacted

The system SHALL represent graph human-in-the-loop pauses as JSON-serializable interrupt payloads with `interrupt_id`, `kind`, `title`, `body`, `data`, `allowed_responses`, and redacted metadata. Supported `kind` values SHALL include `approval`, `edit`, `question`, and `python_approval`.

#### Scenario: Approval interrupt is emitted

- **WHEN** a graph node requests human approval
- **THEN** the backend persists and streams an `interrupt` Kira event with `kind: "approval"`, a stable `interrupt_id`, public title/body text, and allowed approval/rejection responses
- **THEN** the payload does not include raw API keys, raw provider config, or raw LangGraph internals

#### Scenario: Invalid interrupt payload is rejected

- **WHEN** a skill or graph node attempts to emit an interrupt without a supported `kind` or meaningful title/body
- **THEN** graph execution emits a structured `error` event with validation metadata
- **THEN** the run does not wait on an unusable human prompt

### Requirement: Resume requests validate human decisions

The system SHALL expose resume behavior that validates resume payloads against the pending interrupt kind before continuing graph execution.

#### Scenario: Approval resume is accepted

- **WHEN** the active pending interrupt has `kind: "approval"` and the client posts an approve decision with the matching `interrupt_id`
- **THEN** the backend accepts the resume value, persists a `resume` event, and continues the graph using the same `thread_id`

#### Scenario: Mismatched resume is rejected

- **WHEN** the client posts a resume value for an unknown or stale `interrupt_id`
- **THEN** the backend returns a structured validation error
- **THEN** graph execution is not resumed

#### Scenario: Edit resume carries replacement content

- **WHEN** the active pending interrupt has `kind: "edit"` and the client posts edited text
- **THEN** the backend validates the edited text is meaningful and bounded
- **THEN** the graph resumes with the edited value rather than the original suggested value

#### Scenario: Question resume carries answer text

- **WHEN** the active pending interrupt has `kind: "question"` and the client posts an answer
- **THEN** the backend validates the answer against the declared response constraints
- **THEN** the graph receives the answer as the resume value

### Requirement: Resume continues the same durable run

The system SHALL resume interrupted skill graph runs with the same `thread_id`, Stage 04 checkpoint identity, run lock, event sequence, and side-effect ledger context.

#### Scenario: Same thread resumes to completion

- **WHEN** a run is interrupted and the client resumes it with a valid decision
- **THEN** subsequent graph work uses the original `thread_id`
- **THEN** event sequence numbers continue after the persisted interrupt event
- **THEN** completed side-effect ledger entries are reused rather than executed again

#### Scenario: Duplicate resume is rejected

- **WHEN** one executor already holds the run lock for a resume operation
- **THEN** a second concurrent resume attempt returns a structured conflict or current run state
- **THEN** no second graph executor starts for the same `thread_id`

### Requirement: Pending interrupt is inspectable and replayable

The system SHALL include pending interrupt state in frontend-safe run state and replay/debug export payloads.

#### Scenario: State includes pending interrupt

- **WHEN** a graph run is waiting on human input
- **THEN** `GET /api/runs/{thread_id}/state` returns status indicating human input is required and includes the redacted pending interrupt payload

#### Scenario: Replay includes interrupt and resume markers

- **WHEN** a completed HITL run is replayed
- **THEN** the export includes persisted `interrupt` and `resume` events in sequence order
- **THEN** replay does not re-run graph nodes, providers, tools, or side effects

### Requirement: Resume detects inactive-branch conflicts
The resume API SHALL detect when an interrupted `thread_id` belongs to a conversation turn that is no longer on the conversation active parent chain.

#### Scenario: Resume outside active chain conflicts
- **WHEN** a run is interrupted, the conversation is rolled back before that turn, and a client attempts to resume the interrupted `thread_id`
- **THEN** the backend returns a structured resume conflict
- **THEN** no continuation events, transcript parts, provider calls, tool calls, or memory records are created

#### Scenario: Resume inside active chain continues
- **WHEN** an interrupted run's turn remains on the conversation active chain
- **THEN** the resume API continues the existing `thread_id` and turn
- **THEN** no new user message or conversation turn is created

### Requirement: Resume conflict metadata is frontend-safe
The system SHALL return frontend-safe conflict metadata describing the interrupted turn, current active head, and branch transition that caused the conflict.

#### Scenario: Conflict response is redacted
- **WHEN** resume conflict metadata is returned
- **THEN** it includes thread ID, conversation ID, turn ID, current active head ID, and relevant transition ID when available
- **THEN** it excludes raw provider secrets, hidden thinking, and unbounded transcript text

