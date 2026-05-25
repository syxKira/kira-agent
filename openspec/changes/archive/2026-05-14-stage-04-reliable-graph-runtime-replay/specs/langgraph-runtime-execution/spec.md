## MODIFIED Requirements

### Requirement: In-memory Stage 03 execution

The system SHALL replace Stage 03 process-local-only graph execution with reliable Stage 04 graph execution for workflow runs by using checkpointed graph state, stable `thread_id` resume, run attempts, and inspectable terminal state.

#### Scenario: Graph run completes with checkpointing

- **WHEN** a graph run completes successfully
- **THEN** checkpoint state, run attempts, and a terminal projection are persisted for that `thread_id`

#### Scenario: Graph runtime exposes resume foundation

- **WHEN** a graph run fails, stops, or reaches a resumable checkpoint
- **THEN** the system preserves enough checkpoint and projection data to resume or inspect the run with the same `thread_id`

### Requirement: Minimal node reliability metadata

The system SHALL enforce minimal node reliability metadata for runtime policy, including node type, allowed tools, timeout hint, retry hint, side-effect hint, and model usage hint.

#### Scenario: Runtime exposes node metadata

- **WHEN** a workflow is discovered or compiled
- **THEN** node metadata is available to tests and runtime reliability policy without interpreting business-specific node names

#### Scenario: Reliability metadata drives Stage 04 policy

- **WHEN** a node declares timeout, retry, side-effect, or model usage hints
- **THEN** Stage 04 uses those hints to enforce timeout, retry, idempotency, side-effect ledger, and provider attempt behavior

## ADDED Requirements

### Requirement: Stable thread resume cursor

The system SHALL use `thread_id` as the stable cursor for starting, resuming, inspecting, streaming, and replaying graph runs.

#### Scenario: Resume uses same thread

- **WHEN** a run is resumed after a checkpoint
- **THEN** the resumed execution uses the same `thread_id` and graph lineage

#### Scenario: New run gets new thread

- **WHEN** a new run is created rather than resumed
- **THEN** it receives a distinct `thread_id`
