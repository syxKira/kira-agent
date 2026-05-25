## ADDED Requirements

### Requirement: Create local runs

The system SHALL expose a FastAPI `POST /api/runs` endpoint that creates a Stage 01 local run using in-memory state and returns a unique `thread_id`.

#### Scenario: Run creation returns thread identifier

- **WHEN** a client posts a valid Stage 01 run request with prompt text and an optional fixture script name
- **THEN** the response includes a unique `thread_id`, initial run status, and enough metadata for the frontend to open the event stream

#### Scenario: Run creation does not require network credentials

- **WHEN** a client creates a run using the fixture provider
- **THEN** the backend does not require external network access or an API key

### Requirement: Stream run events over SSE

The system SHALL expose `GET /api/runs/{thread_id}/events` as an SSE endpoint for normalized Stage 01 run events.

#### Scenario: Existing run streams events

- **WHEN** a client opens the SSE endpoint for an existing `thread_id`
- **THEN** the backend streams ordered events with `type`, `thread_id`, `seq`, and `data` fields

#### Scenario: Missing run returns an API error

- **WHEN** a client opens the SSE endpoint for an unknown `thread_id`
- **THEN** the backend returns a clear not-found API error instead of starting an implicit run

### Requirement: Limit Stage 01 persistence

The system SHALL keep Stage 01 run state in process memory and SHALL NOT add checkpoint, resume, replay, lock, idempotency, or side-effect ledger behavior.

#### Scenario: Stage 04 behavior remains unavailable

- **WHEN** Stage 01 run endpoints are implemented
- **THEN** no checkpoint, resume, replay, run-lock, idempotency, or side-effect-ledger endpoint is exposed

### Requirement: Document local development commands

The system SHALL document how to start the backend and frontend locally for Stage 01.

#### Scenario: Developer follows startup instructions

- **WHEN** a developer follows the documented backend and frontend commands
- **THEN** the FastAPI app and Vite app start independently and the frontend can call the local API
