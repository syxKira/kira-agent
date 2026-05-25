# langgraph-runtime-execution Specification

## Purpose
TBD - created by archiving change stage-03-skill-driven-langgraph-runtime. Update Purpose after archive.
## Requirements
### Requirement: Generic LangGraph runtime

The system SHALL provide a backend graph runtime that compiles skill-defined workflows through LangGraph `StateGraph` without hardcoding business-specific node names or workflow sequences in Kira core.

#### Scenario: Test workflow compiles

- **WHEN** the runtime receives a valid Stage 03 workflow spec from the test skill
- **THEN** it compiles the workflow into a LangGraph graph
- **THEN** Kira core does not require business-specific node names to compile the graph

#### Scenario: Core rejects business workflow assumptions

- **WHEN** a workflow uses arbitrary valid node names
- **THEN** runtime behavior is driven by the workflow spec rather than special cases in Kira core

### Requirement: Workflow validation before compilation

The system SHALL validate workflow declarations before compiling them and SHALL reject missing entrypoints, duplicate nodes, invalid edge targets, unsupported node types, and unsupported graph declarations.

#### Scenario: Invalid edge target is rejected

- **WHEN** a workflow edge references a node that is not declared
- **THEN** compilation fails with a structured graph validation error

#### Scenario: Unsupported declaration is rejected

- **WHEN** a workflow declaration uses an unsupported schema or node type
- **THEN** compilation fails with a structured graph validation error

### Requirement: Conditional edge execution

The system SHALL support conditional edges for branch, loop, and termination decisions within skill-defined workflows.

#### Scenario: Conditional branch terminates

- **WHEN** a workflow condition selects a terminal branch
- **THEN** the graph run ends and emits a completion event

#### Scenario: Conditional branch selects tool path

- **WHEN** a workflow condition selects a tool node branch
- **THEN** the graph run executes the tool path through the compiled graph

### Requirement: Run context graph state

The system SHALL initialize graph state from run context, including prompt text, thread ID, selected skill ID, project root when provided, redacted provider metadata, selected model, and fixture fallback status.

#### Scenario: Graph state receives redacted provider metadata

- **WHEN** a graph run starts after provider selection
- **THEN** graph state includes redacted provider metadata and selected model information
- **THEN** graph state does not include raw API keys or raw provider config objects

#### Scenario: Request provider override reaches graph context

- **WHEN** a graph run is created with request-level provider or model override
- **THEN** the selected provider/model metadata in graph state reflects the override decision in redacted form

### Requirement: Minimal node reliability metadata

The system SHALL enforce minimal node reliability metadata for runtime policy, including node type, allowed tools, timeout hint, retry hint, side-effect hint, and model usage hint.

#### Scenario: Runtime exposes node metadata

- **WHEN** a workflow is discovered or compiled
- **THEN** node metadata is available to tests and runtime reliability policy without interpreting business-specific node names

#### Scenario: Reliability metadata drives Stage 04 policy

- **WHEN** a node declares timeout, retry, side-effect, or model usage hints
- **THEN** Stage 04 uses those hints to enforce timeout, retry, idempotency, side-effect ledger, and provider attempt behavior

### Requirement: In-memory Stage 03 execution

The system SHALL replace Stage 03 process-local-only graph execution with reliable Stage 04 graph execution for workflow runs by using checkpointed graph state, stable `thread_id` resume, run attempts, and inspectable terminal state.

#### Scenario: Graph run completes with checkpointing

- **WHEN** a graph run completes successfully
- **THEN** checkpoint state, run attempts, and a terminal projection are persisted for that `thread_id`

#### Scenario: Graph runtime exposes resume foundation

- **WHEN** a graph run fails, stops, or reaches a resumable checkpoint
- **THEN** the system preserves enough checkpoint and projection data to resume or inspect the run with the same `thread_id`

### Requirement: Stable thread resume cursor

The system SHALL use `thread_id` as the stable cursor for starting, resuming, inspecting, streaming, and replaying graph runs.

#### Scenario: Resume uses same thread

- **WHEN** a run is resumed after a checkpoint
- **THEN** the resumed execution uses the same `thread_id` and graph lineage

#### Scenario: New run gets new thread

- **WHEN** a new run is created rather than resumed
- **THEN** it receives a distinct `thread_id`

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

