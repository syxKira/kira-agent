## ADDED Requirements

### Requirement: Resume interrupted local runs

The system SHALL expose `POST /api/runs/{thread_id}/resume` for interrupted checkpointed skill graph runs.

#### Scenario: Resume endpoint accepts valid decision

- **WHEN** a client posts a valid resume value for the active pending interrupt on an existing `thread_id`
- **THEN** the backend returns accepted resume metadata and continues graph execution for that `thread_id`

#### Scenario: Resume endpoint rejects missing interrupt

- **WHEN** a client posts to the resume endpoint for a run with no pending interrupt
- **THEN** the backend returns a structured validation or conflict error
- **THEN** no new graph work is scheduled

#### Scenario: Resume endpoint rejects unknown thread

- **WHEN** a client posts to the resume endpoint for an unknown `thread_id`
- **THEN** the backend returns a clear not-found API error

### Requirement: SSE supports reconnect cursors for HITL runs

The system SHALL support `after_seq` cursor replay for HITL graph event streams.

#### Scenario: Reconnect replays missed events

- **WHEN** a client reconnects to `GET /api/runs/{thread_id}/events?after_seq=<n>`
- **THEN** the backend first streams persisted events with sequence greater than `<n>`
- **THEN** missed interrupt, resume, tool, and completion events are delivered without duplicates

#### Scenario: Reconnect does not rerun graph work

- **WHEN** a client reconnects only to read events already persisted for a completed or waiting run
- **THEN** the backend does not invoke provider calls, tools, side effects, or new graph nodes

### Requirement: Run APIs expose safe HITL state

The system SHALL expose pending interrupt and resume status through frontend-safe API payloads without exposing raw secrets or runtime internals.

#### Scenario: Run creation response identifies resume URL

- **WHEN** a skill graph run is created
- **THEN** the run creation response includes enough public metadata for the frontend to stream events and submit resume values when interrupted

#### Scenario: State response includes HITL status

- **WHEN** a run is waiting on human input
- **THEN** the state endpoint reports a waiting status and the current pending interrupt summary
- **THEN** the payload excludes raw API keys and raw provider config objects
