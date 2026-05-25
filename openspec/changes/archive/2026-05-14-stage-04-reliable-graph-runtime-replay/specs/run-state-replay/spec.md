## ADDED Requirements

### Requirement: Run state projection endpoint

The system SHALL expose `GET /api/runs/{thread_id}/state` returning a frontend-safe projection of a run.

#### Scenario: Existing run state is returned
- **WHEN** a client requests state for a known `thread_id`
- **THEN** the response includes status, selected skill, latest event sequence, workflow summary, provider/model metadata, lock status, attempts, tool summaries, side-effect summaries, and pending interrupt when present

#### Scenario: Missing run state is structured
- **WHEN** a client requests state for an unknown `thread_id`
- **THEN** the backend returns a structured not-found error

### Requirement: Debug replay export

The system SHALL provide a replay or debug export that reconstructs persisted events, checkpoint summaries, tool summaries, provider attempt summaries, side-effect ledger summaries, audit references, and repair notes for a run.

#### Scenario: Replay is read-only
- **WHEN** a replay/export is requested
- **THEN** the backend reads stored records and does not re-run graph nodes, tools, providers, or side effects

#### Scenario: Replay includes redacted provider data
- **WHEN** a replay/export includes provider attempts
- **THEN** provider metadata is redacted and contains no raw API keys

### Requirement: SSE replay cursor

The system SHALL support replaying missed persisted events before live SSE events when a client reconnects with an event sequence cursor.

#### Scenario: Reconnect gets missed events
- **WHEN** a client reconnects with the last seen event sequence
- **THEN** the backend streams persisted events after that sequence before live events

#### Scenario: Reconnect preserves order
- **WHEN** missed events and live events are streamed together
- **THEN** event sequence values remain monotonically increasing for the `thread_id`

### Requirement: Corrupted or missing checkpoint handling

The system SHALL classify missing or corrupted checkpoint state as a structured invariant failure and SHALL keep debug export available when possible.

#### Scenario: Missing checkpoint returns invariant error
- **WHEN** resume requires a checkpoint that cannot be found
- **THEN** the run is marked failed with an `invariant_error` class

#### Scenario: Corrupted checkpoint remains inspectable
- **WHEN** checkpoint decoding fails
- **THEN** the state endpoint and debug export expose the failure summary without crashing the backend

### Requirement: Repair notes and constrained repair state

The system SHALL allow failed runs to record repair notes and MAY allow repair of explicitly permitted state fields before resume.

#### Scenario: Repair note is stored
- **WHEN** a developer records a repair note for a failed run
- **THEN** replay/export includes the note with timestamp and author/source metadata

#### Scenario: Unsafe repair is rejected
- **WHEN** a repair request attempts to edit provider secrets, ledger status, event history, or arbitrary workflow internals
- **THEN** the backend rejects the request with a structured validation error
