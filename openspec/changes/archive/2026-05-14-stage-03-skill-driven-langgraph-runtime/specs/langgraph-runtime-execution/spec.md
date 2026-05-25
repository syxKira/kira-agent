## ADDED Requirements

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

The system SHALL preserve minimal node metadata for future reliability stages, including node type, allowed tools, timeout hint, retry hint, side-effect hint, and model usage hint.

#### Scenario: Runtime exposes node metadata

- **WHEN** a workflow is discovered or compiled
- **THEN** node metadata is available to tests and future runtime policy without interpreting business-specific node names

#### Scenario: Reliability metadata is informational in Stage 03

- **WHEN** a node declares retry or side-effect hints
- **THEN** Stage 03 records and exposes the hints but does not implement durable retry, idempotency, or side-effect reuse

### Requirement: In-memory Stage 03 execution

The system SHALL keep Stage 03 graph execution process-local and non-durable.

#### Scenario: Graph run completes without checkpointing

- **WHEN** a graph run completes successfully
- **THEN** no SQLite checkpoint, replay record, run lock, or side-effect ledger entry is required

#### Scenario: Graph runtime does not expose resume

- **WHEN** a graph run fails or stops in Stage 03
- **THEN** the system does not promise durable resume or replay behavior
