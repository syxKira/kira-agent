# run-state-replay Specification

## Purpose
TBD - created by archiving change stage-04-reliable-graph-runtime-replay. Update Purpose after archive.
## Requirements
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

### Requirement: Replay includes memory usage summaries
The run state and replay/debug export APIs SHALL include frontend-safe summaries of memory retrieval, injected memory citations, and extraction candidates associated with a run.

#### Scenario: Replay shows injected memory
- **WHEN** replay/debug export is requested for a run with injected memory
- **THEN** the export includes memory IDs, citation IDs, scopes, types, score reasons, and redacted source summaries

#### Scenario: Replay omits raw memory secrets
- **WHEN** replay/debug export includes memory summaries
- **THEN** raw memory secrets, raw provider secrets, and unbounded candidate text are absent

### Requirement: Replay does not rerun memory extraction
The replay/debug export SHALL read persisted memory summaries and SHALL NOT rerun memory retrieval, extraction, providers, tools, or lifecycle actions.

#### Scenario: Replay is read-only for memory
- **WHEN** a completed run's replay is requested
- **THEN** no new memory record, candidate, citation, event, or retrieval trace is created

### Requirement: Run state includes conversation linkage
The run state projection endpoint SHALL include frontend-safe `conversation_id`, `turn_id`, and transcript message linkage when a run belongs to a conversation.

#### Scenario: State shows conversation link
- **WHEN** a client requests state for a conversation-backed run
- **THEN** the state response includes `conversation_id`, `turn_id`, user message ID, assistant message ID when available, and no raw provider secrets

### Requirement: Replay includes transcript summaries without side effects
The replay/debug export SHALL include saved conversation and transcript linkage for a run and SHALL NOT rebuild transcript context or append transcript parts.

#### Scenario: Replay is read-only for transcript
- **WHEN** replay/debug export is requested for a conversation-backed run
- **THEN** the export reads persisted conversation/turn/message references
- **THEN** no new transcript message, transcript part, context trace, provider call, tool call, memory record, or retrieval trace is created

### Requirement: SSE reconnect does not duplicate transcript text
The system SHALL avoid appending duplicate assistant transcript text when a client reconnects to read persisted SSE events.

#### Scenario: Reconnect replays events read-only
- **WHEN** a client reconnects to an existing event stream with `after_seq`
- **THEN** replayed persisted events are streamed to the client
- **THEN** replayed events do not append duplicate transcript parts

### Requirement: Run state includes compaction and replacement summaries
The run state projection endpoint SHALL include frontend-safe compaction summary and tool-output replacement references when a run used them for transcript context.

#### Scenario: State shows summary linkage
- **WHEN** a client requests state for a run that used a compaction summary
- **THEN** the state response includes summary ID, conversation ID, source range, stale status at run time, and budget metadata
- **THEN** the response excludes raw provider secrets and hidden thinking

#### Scenario: State shows replacement linkage
- **WHEN** a client requests state for a run that used a replacement stub
- **THEN** the state response includes replacement ID, source part ID, reason, omitted count, hash or hash prefix, and bounded summary metadata
- **THEN** raw replaced output is not exposed

### Requirement: Replay is read-only for compaction and replacement
The replay/debug export SHALL include saved compaction and replacement metadata without regenerating summaries, resolving raw replacement blobs, mutating transcript state, or creating memory records.

#### Scenario: Replay does not regenerate compaction
- **WHEN** replay/debug export is requested for a run that used compaction
- **THEN** replay reads saved summary metadata
- **THEN** replay does not call providers, create summaries, append transcript parts, or update stale status

#### Scenario: Replay does not resolve replacement blob
- **WHEN** replay/debug export is requested for a run with replacement records
- **THEN** replay returns saved frontend-safe replacement summary metadata
- **THEN** replay does not read raw replacement blobs, call tools, or expose raw replaced output

### Requirement: Replay records stale state as observed by the run
The replay/debug export SHALL report whether a compaction summary or replacement record was included, omitted, truncated, or stale at the time of the run context build.

#### Scenario: Replay preserves historical context decision
- **WHEN** a summary becomes stale after a completed run
- **THEN** replay for the completed run still shows the saved context decision from that run
- **THEN** replay does not rebuild context using the current summary status

### Requirement: Run state includes branch metadata
The run state projection endpoint SHALL include frontend-safe branch metadata when a run belongs to a forked or rolled-back conversation.

#### Scenario: State shows branch context
- **WHEN** a client requests state for a run after fork or rollback
- **THEN** the response includes conversation ID, turn ID, active head ID at run creation, fork source or rollback transition metadata when available, and no raw provider secrets

### Requirement: Replay is read-only for branch state
The replay/debug export SHALL include saved fork/rollback and active-head metadata without mutating conversation active head, creating branch records, or rebuilding transcript context.

#### Scenario: Replay does not change active head
- **WHEN** replay/debug export is requested for a branch-aware run
- **THEN** replay reads saved branch metadata
- **THEN** replay does not update active head, create transcript parts, create branch records, call providers, call tools, or create memory records

### Requirement: Replay preserves historical branch decision
The replay/debug export SHALL report active-head and inactive-branch context decisions as observed by the run.

#### Scenario: Replay uses saved run branch view
- **WHEN** a conversation active head changes after a completed run
- **THEN** replay for the completed run still shows the active head and context decisions saved for that run
- **THEN** replay does not rebuild context using the current active head

